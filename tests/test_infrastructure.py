"""File and Bitwarden adapters; fictional credentials only."""
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.domain.credential import Credential  # noqa: E402
from backend.password_checker.infrastructure.bitwarden import BITWARDEN_FIELDS, write_bitwarden_csv  # noqa: E402
from backend.password_checker.infrastructure.csv_reader import read_upload  # noqa: E402

class BitwardenTests(unittest.TestCase):
    def test_writes_header_and_login_rows(self):
        buffer = io.StringIO(newline='')
        count = write_bitwarden_csv(buffer, [Credential('chrome', 2, 'Site', 'https://a.invalid', 'u', 'fake,pw', 'n')])
        lines = buffer.getvalue().splitlines()
        self.assertEqual(count, 1)
        self.assertEqual(lines[0], ','.join(BITWARDEN_FIELDS))
        self.assertEqual(lines[1], ',,login,Site,n,,0,https://a.invalid,u,"fake,pw",')


class UploadReaderTests(unittest.TestCase):
    def test_detects_firefox_without_name_hint(self):
        data = ('url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged\n'
                'https://example.org/login,alice,fictional-abc-123,,,,,,\n').encode()
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
