"""CSV parsing tests with fictional credentials."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.infrastructure.csv_reader import read_export


class PasswordCheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.chrome = self.root / 'chrome.csv'
        self.brave = self.root / 'brave.csv'
        self.firefox = self.root / 'firefox.csv'
        self._csv(self.chrome,
                  ['name', 'url', 'username', 'password', 'note'],
                  [['GitHub', 'https://github.com/login', 'alice', 'fake-correct-123456', 'nota, con coma\n y salto de linea'],
                   ['GitHub', 'https://github.com/login', 'alice', 'fake-old-123456789', 'vieja'],
                   ['Otro', 'https://service.invalid', 'bob', 'fake-correct-123456', '']])
        self._csv(self.brave,
                  ['name', 'url', 'username', 'password', 'note'],
                  [['GH', 'https://github.com/login', 'alice', 'fake-correct-123456', 'otra nota']])
        self._csv(self.firefox,
                  ['url', 'username', 'password', 'httpRealm', 'formActionOrigin', 'guid',
                   'timeCreated', 'timeLastUsed', 'timePasswordChanged'],
                  [['https://github.com/login', 'alice', 'fake-correct-123456', '',
                    'https://github.com', 'guid-ficticio', '1710000', '1720000', '1730000'],
                   ['https://basic.invalid/path', 'bob', 'fake-strong-123456', 'Area privada',
                    '', 'guid-ficticio-2', '1710001', '1720001', '1730001']])

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
        diagnostics = []
        rows = read_export('chrome', self.chrome, diagnostics=diagnostics)
        self.assertEqual(rows[0].name, 'Red social,mensajero')
        self.assertEqual(rows[0].username, 'user42')
        self.assertEqual(rows[0].password, 'fake-password-123')
        self.assertEqual(len(diagnostics), 1)

    def test_android_uri_no_title_comma(self):
        uri = 'android://FAKE@com.example.shop/'
        self._csv(self.chrome, ['name','url','username','password','note'],
                  [['Shop',uri,'user42','fake-password-123','']])
        rows = read_export('chrome', self.chrome)
        self.assertEqual(rows[0].url, uri)
        self.assertEqual(rows[0].password, 'fake-password-123')

    def test_shifted_title_with_missing_trailing_note(self):
        self.chrome.write_text(
            'name,url,username,password,note\n'
            'Red social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123\n',
            encoding='utf-8')
        rows = read_export('chrome', self.chrome)
        self.assertEqual(rows[0].name, 'Red social,mensajero')
        self.assertEqual(rows[0].note, '')

    def test_malformed_and_ambiguous_rows_are_rejected_without_secrets(self):
        for row in ('Site,https://test.invalid,alice,fake-PW,note,extra',
                    'Site,https://test.invalid,alice'):
            self.chrome.write_text('name,url,username,password,note\n' + row + '\n', encoding='utf-8')
            with self.assertRaises(ValueError) as error:
                read_export('chrome', self.chrome)
            self.assertNotIn('fake-PW', str(error.exception))

    def test_note_repair_and_missing_trailing_note(self):
        self.chrome.write_text('name,url,username,password,note\nSite,https://test.invalid,alice,fake-PW,note,extra\n', encoding='utf-8')
        diagnostics = []
        rows = read_export('chrome', self.chrome, repair_extra_notes=True, diagnostics=diagnostics)
        self.assertEqual((rows[0].password, rows[0].note), ('fake-PW', 'note,extra'))
        self.assertTrue(diagnostics)
        self.chrome.write_text('name,url,username,password,note\nSite,https://test.invalid,alice,fake-PW\n', encoding='utf-8')
        diagnostics = []
        self.assertEqual(read_export('chrome', self.chrome, diagnostics=diagnostics)[0].note, '')
        self.assertTrue(diagnostics)

    def test_comma_in_quoted_password(self):
        self._csv(self.chrome, ['name', 'url', 'username', 'password', 'note'],
                  [['Site', 'https://test.invalid', 'alice', 'fake,with,commas', 'note,commas']])
        row = read_export('chrome', self.chrome)[0]
        self.assertEqual((row.password, row.note), ('fake,with,commas', 'note,commas'))

    def test_repair_rejects_misaligned_uri(self):
        self.chrome.write_text('name,url,username,password,note\nRed,social,mensajero,android://FAKE@com.example.social/,user42,fake-password-123,\n', encoding='utf-8')
        with self.assertRaises(ValueError) as error:
            read_export('chrome', self.chrome, repair_extra_notes=True)
        self.assertIn('URI fuera de su columna', str(error.exception))
        self.assertNotIn('fake-password-123', str(error.exception))

    def test_semicolon_diagnostic(self):
        self.chrome.write_text('name;url;username;password;note\nSite;https://test.invalid;alice;abc;note\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'punto y coma'):
            read_export('chrome', self.chrome)


if __name__ == '__main__':
    unittest.main()
