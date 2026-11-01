"""Bitwarden adapter tests with fictional credentials."""
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.domain.credential import Credential  # noqa: E402
from backend.password_checker.infrastructure.bitwarden import BITWARDEN_FIELDS, write_bitwarden_csv  # noqa: E402

class BitwardenTests(unittest.TestCase):
    def test_writes_header_and_login_rows(self):
        buffer = io.StringIO(newline='')
        count = write_bitwarden_csv(buffer, [Credential('chrome', 2, 'Site', 'https://a.invalid', 'u', 'fake,pw', 'n')])
        lines = buffer.getvalue().splitlines()
        self.assertEqual(count, 1)
        self.assertEqual(lines[0], ','.join(BITWARDEN_FIELDS))
        self.assertEqual(lines[1], ',,login,Site,n,,0,https://a.invalid,u,"fake,pw",')


if __name__ == '__main__':
    unittest.main()
