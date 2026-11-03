"""Bitwarden adapter tests with fictional credentials."""
import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.domain.credential import Credential
from backend.password_checker.infrastructure.bitwarden import BITWARDEN_FIELDS, write_bitwarden_csv


class BitwardenTests(unittest.TestCase):
    def test_writes_header_and_login_rows(self):
        buffer = io.StringIO(newline='')
        count = write_bitwarden_csv(buffer, [Credential('chrome', 2, 'Site', 'https://a.invalid', 'u', 'fake,pw', 'n')])
        lines = buffer.getvalue().splitlines()
        self.assertEqual(count, 1)
        self.assertEqual(lines[0], ','.join(BITWARDEN_FIELDS))
        self.assertEqual(lines[1], ',,login,Site,n,,0,https://a.invalid,u,"fake,pw",')

    def test_writes_the_totp_exactly_as_an_otpauth_uri(self):
        # Bitwarden's importer stores login_totp verbatim and its SDK parses otpauth:// keys.
        totp = 'otpauth://totp/Example:u?secret=FICTIONALSECRET&issuer=Example,Inc&digits=8'
        buffer = io.StringIO(newline='')
        write_bitwarden_csv(buffer, [Credential('safari', 2, 'Site', 'https://a.invalid', 'u', 'fake-pw', '', totp),
                                     Credential('safari', 3, 'Other', 'https://b.invalid', 'v', 'fake-pw', '')])
        rows = list(csv.DictReader(io.StringIO(buffer.getvalue())))
        self.assertEqual([row['login_totp'] for row in rows], [totp, ''])


if __name__ == '__main__':
    unittest.main()
