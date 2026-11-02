"""CSV parsing tests with fictional credentials."""
import csv
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.infrastructure.csv_reader import (
    detect_format_and_origin,
    read_upload,
)


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

    def assert_readable_error(self, content, secret):
        """Python's csv.Error becomes a ValueError that names the line, never the cell."""
        with self.assertRaises(ValueError) as error:
            read_upload('chrome.csv', content)
        self.assertNotIsInstance(error.exception, csv.Error)
        self.assertIn('formato no válido', str(error.exception))
        self.assertNotIn(secret, str(error.exception))
        return str(error.exception)

    def test_bad_quoting_in_a_row_is_a_readable_error(self):
        message = self.assert_readable_error(
            b'name,url,username,password,note\n'
            b'Ok,https://ok.invalid,bob,fictional-ok-123,\n'
            b'Site,https://test.invalid,alice,"fictional-secret-1"x,\n', 'fictional-secret-1')
        self.assertIn('línea 3', message)

    def test_bad_quoting_in_the_header_is_a_readable_error(self):
        self.assert_readable_error(b'name,"url"fictional-header,username,password,note\n', 'fictional-header')

    def test_field_over_the_csv_reader_limit_is_a_readable_error(self):
        huge = b'fictional-huge-' + b'x' * csv.field_size_limit()
        self.assert_readable_error(b'name,url,username,password,note\nSite,https://a.invalid,al,pw,' + huge + b'\n',
                                   'fictional-huge-')
        self.assert_readable_error(b'name,url,username,password,' + huge + b'\n', 'fictional-huge-')

    def test_valid_quoted_commas_and_line_breaks_still_import(self):
        source, rows = read_upload('chrome.csv', b'name,url,username,password,note\n'
                                   b'"A, B",https://a.invalid,alice,"fictional,pw","line one\nline two"\n')
        self.assertEqual((source, rows[0].name, rows[0].password, rows[0].note),
                         ('chrome', 'A, B', 'fictional,pw', 'line one\nline two'))

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


CHROMIUM = ['name', 'url', 'username', 'password', 'note']
FIREFOX = ['url', 'username', 'password', 'httpRealm', 'formActionOrigin', 'guid',
           'timeCreated', 'timeLastUsed', 'timePasswordChanged']
GENERIC = ['url', 'username', 'password']


class FormatOriginTests(unittest.TestCase):
    """The format says how to read a CSV; the origin only says where it came from."""

    def test_format_comes_from_the_headers_and_origin_from_the_name(self):
        cases = [
            (CHROMIUM, 'brave.csv', ('chromium', 'brave')),
            (CHROMIUM, 'chrome.csv', ('chromium', 'chrome')),
            (CHROMIUM, 'mis_contrasenas.csv', ('chromium', 'unknown')),
            (CHROMIUM, 'firefox.csv', ('chromium', 'unknown')),
            (FIREFOX, 'brave.csv', ('firefox', 'firefox')),
            (GENERIC, 'chrome.csv', ('generic', 'unknown')),
            (GENERIC + ['guid'], 'export.csv', ('generic', 'unknown')),
            (['Name', ' URL ', 'User_Name', 'Password'], 'Brave Passwords.csv', ('chromium', 'brave')),
            (['url', 'username', 'password', 'Notes'], 'CHROME export.csv', ('chromium', 'chrome')),
        ]
        for headers, name, expected in cases:
            with self.subTest(headers=headers, name=name):
                self.assertEqual(detect_format_and_origin(headers, name), expected)

    def test_renaming_a_file_only_changes_the_inferred_origin(self):
        # A missing trailing note is a Chromium repair: it must not depend on the name.
        data = b'name,url,username,password,note\nSite,https://test.invalid,alice,fake-PW\n'
        read = {name: read_upload(name, data) for name in (
            'chrome.csv', 'brave.csv', 'mis_contrasenas.csv', 'my-bravery-awards-backup-2026-11-02.csv')}
        self.assertEqual({name: origin for name, (origin, _) in read.items()}, {
            'chrome.csv': 'chrome', 'brave.csv': 'brave', 'mis_contrasenas.csv': 'unknown',
            'my-bravery-awards-backup-2026-11-02.csv': 'brave'})
        for name, (origin, rows) in read.items():
            with self.subTest(name=name):
                self.assertEqual([row.source for row in rows], [origin])
        credentials = {tuple(replace(row, source='') for row in rows) for _, rows in read.values()}
        self.assertEqual(len(credentials), 1)
        self.assertEqual(next(iter(credentials))[0].note, '')

    def test_generic_csv_imports_with_an_unknown_origin(self):
        origin, rows = read_upload('chrome.csv', b'url,username,password\nhttps://a.invalid,alice,fake-PW\n')
        self.assertEqual(origin, 'unknown')
        self.assertEqual([(row.source, row.url, row.username) for row in rows],
                         [('unknown', 'https://a.invalid', 'alice')])


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
