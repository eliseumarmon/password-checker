"""CSV parsing tests with fictional credentials."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.infrastructure.csv_reader import read_upload


class CsvUploadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.chrome = self.root / 'chrome.csv'

    @staticmethod
    def _csv(path, headers, rows):
        with path.open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)

    def test_android_uri_unquoted_comma_in_title(self):
        self.chrome.write_text(
            'name,url,username,password,note\n'
            'Red social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123,\n',
            encoding='utf-8')
        rows = read_upload('chrome.csv', self.chrome.read_bytes())[1]
        self.assertEqual(rows[0].name, 'Red social,mensajero')
        self.assertEqual(rows[0].username, 'user42')
        self.assertEqual(rows[0].password, 'fake-password-123')

    def test_android_uri_no_title_comma(self):
        uri = 'android://FAKE@com.example.shop/'
        self._csv(self.chrome, ['name','url','username','password','note'],
                  [['Shop',uri,'user42','fake-password-123','']])
        rows = read_upload('chrome.csv', self.chrome.read_bytes())[1]
        self.assertEqual(rows[0].url, uri)
        self.assertEqual(rows[0].password, 'fake-password-123')

    def test_shifted_title_with_missing_trailing_note(self):
        self.chrome.write_text(
            'name,url,username,password,note\n'
            'Red social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123\n',
            encoding='utf-8')
        rows = read_upload('chrome.csv', self.chrome.read_bytes())[1]
        self.assertEqual(rows[0].name, 'Red social,mensajero')
        self.assertEqual(rows[0].note, '')

    def test_malformed_and_ambiguous_rows_are_rejected_without_secrets(self):
        for row in ('Site,https://test.invalid,alice,fake-PW,note,extra',
                    'Site,https://test.invalid,alice'):
            self.chrome.write_text('name,url,username,password,note\n' + row + '\n', encoding='utf-8')
            with self.assertRaises(ValueError) as error:
                read_upload('chrome.csv', self.chrome.read_bytes())[1]
            self.assertNotIn('fake-PW', str(error.exception))

    def test_missing_trailing_note_is_completed(self):
        self.chrome.write_text('name,url,username,password,note\nSite,https://test.invalid,alice,fake-PW\n', encoding='utf-8')
        self.assertEqual(read_upload('chrome.csv', self.chrome.read_bytes())[1][0].note, '')

    def test_comma_in_quoted_password(self):
        self._csv(self.chrome, ['name', 'url', 'username', 'password', 'note'],
                  [['Site', 'https://test.invalid', 'alice', 'fake,with,commas', 'note,commas']])
        row = read_upload('chrome.csv', self.chrome.read_bytes())[1][0]
        self.assertEqual((row.password, row.note), ('fake,with,commas', 'note,commas'))

    def test_rejects_misaligned_uri(self):
        self.chrome.write_text('name,url,username,password,note\nRed,social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123,\n', encoding='utf-8')
        with self.assertRaises(ValueError) as error:
            read_upload('chrome.csv', self.chrome.read_bytes())[1]
        self.assertIn('URI fuera de su columna', str(error.exception))
        self.assertNotIn('fake-password-123', str(error.exception))

    def test_semicolon_diagnostic(self):
        self.chrome.write_text('name;url;username;password;note\nSite;https://test.invalid;alice;abc;note\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'punto y coma'):
            read_upload('chrome.csv', self.chrome.read_bytes())[1]

    def test_bom_quoted_comma_and_multiline_note(self):
        data = ('name,url,username,password,note\n'
                'Ejemplo,https://example.invalid/login,user,"fake,secret","linea 1\nlinea 2"\n')
        source, rows = read_upload('chrome.csv', data.encode('utf-8-sig'))
        self.assertEqual(source, 'chrome')
        self.assertEqual((rows[0].password, rows[0].note), ('fake,secret', 'linea 1\nlinea 2'))

    def test_firefox_realm_is_preserved_in_note(self):
        data = (b'url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged\n'
                b'https://basic.invalid/path,bob,fake-secret,Private,,,,,\n')
        source, rows = read_upload('export.csv', data)
        self.assertEqual(source, 'firefox')
        self.assertEqual(rows[0].note, 'Firefox HTTP realm: Private')

    def test_firefox_realm_header_variants_detect_and_preserve_realm(self):
        for header in ('http_realm', 'HTTP_REALM', 'Http-Realm', ' httpRealm ', 'http realm', '\thttp\tRealm\t'):
            with self.subTest(header=header):
                data = (f'url,username,password,note,{header}\n'
                        'https://basic.invalid/path,bob,fictional-secret,Existing note,Private realm\n').encode()
                source, rows = read_upload('Brave Passwords.csv', data)
                self.assertEqual(source, 'firefox')
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0].source, 'firefox')
                self.assertEqual(rows[0].url, 'https://basic.invalid/path')
                self.assertEqual((rows[0].username, rows[0].password), ('bob', 'fictional-secret'))
                self.assertEqual(rows[0].note, 'Existing note\n\nFirefox HTTP realm: Private realm')

    def test_realm_like_header_does_not_detect_firefox(self):
        data = (b'url,username,password,note,http_realm_extra\n'
                b'https://basic.invalid/path,bob,fictional-secret,Existing note,Private realm\n')
        source, rows = read_upload('Brave Passwords.csv', data)
        self.assertEqual(source, 'brave')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].source, 'brave')
        self.assertEqual(rows[0].note, 'Existing note')


class UploadReaderTests(unittest.TestCase):
    def test_detects_firefox_without_name_hint(self):
        data = (b'url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged\n'
                b'https://example.org/login,alice,fictional-abc-123,,,,,,\n')
        source, rows = read_upload('passwords.csv', data)
        self.assertEqual(source, 'firefox')
        self.assertEqual(len(rows), 1)

    def test_brave_by_file_name_and_null_bytes_rejected(self):
        data = b'name,url,username,password,note\nA,https://example.org,u,fake-123,\n'
        self.assertEqual(read_upload('Brave Passwords.csv', data)[0], 'brave')
        with self.assertRaises(ValueError):
            read_upload('chrome.csv', b'\x00')


if __name__ == '__main__':
    unittest.main()
