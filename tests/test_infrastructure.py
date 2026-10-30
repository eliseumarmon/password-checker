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
from backend.password_checker.infrastructure.files import create_new_file  # noqa: E402

CREATE_OPTIONS = {'same_as_protected_error': 'protected', 'missing_folder_error': 'missing {}', 'newline': '\n'}


class CreateNewFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_creates_file_with_content(self):
        target = self.root / 'new.md'
        created = create_new_file(target, [], lambda f: f.write('hola'), **CREATE_OPTIONS)
        self.assertEqual(created, target)
        self.assertEqual(target.read_text(encoding='utf-8'), 'hola')

    def test_never_overwrites_existing_or_protected_files(self):
        existing = self.root / 'existing.csv'
        existing.write_text('original', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            create_new_file(existing, [], lambda f: f.write('x'), **CREATE_OPTIONS)
        with self.assertRaisesRegex(ValueError, '^protected$'):
            create_new_file(existing, [existing], lambda f: f.write('x'), **CREATE_OPTIONS)
        self.assertEqual(existing.read_text(encoding='utf-8'), 'original')

    def test_missing_folder_message_names_folder(self):
        with self.assertRaisesRegex(ValueError, '^missing .*nope$'):
            create_new_file(self.root / 'nope' / 'x.md', [], lambda f: f.write('x'), **CREATE_OPTIONS)

    def test_partial_file_removed_when_writing_fails(self):
        target = self.root / 'partial.csv'

        def fail(file):
            file.write('half')
            raise RuntimeError('disk full')
        with self.assertRaises(RuntimeError):
            create_new_file(target, [], fail, **CREATE_OPTIONS)
        self.assertFalse(target.exists())


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
