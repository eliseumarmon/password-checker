"""Untrusted session snapshots use only fabricated credentials."""
from copy import deepcopy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.password_checker.application.candidate import Candidate
from backend.password_checker.application.session_snapshot import from_payload
from backend.password_checker.application.workspace import ImportedFile, Workspace
from backend.password_checker.domain.credential import ORIGINS, Credential


class SessionSnapshotLimitTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        original = Credential('chrome', 2, 'Example', 'https://example.invalid/',
                              'user', 'fake-password-123456', 'note')
        record = Candidate.from_source(original)
        self.workspace._records[record.id] = record
        self.workspace._files = [{'name': 'example.csv', 'source': 'chrome', 'count': 1}]
        self.payload = self.workspace.serialize()

    def test_record_count_limit(self):
        record = self.payload['records'][0]
        maximum = [dict(record, id=f'row-{index}') for index in range(100_000)]
        self.assertEqual(len(from_payload({**self.payload, 'records': maximum})[0]), 100_000)
        for records in ([], self.payload['records'] * 100_001):
            with self.subTest(count=len(records)), self.assertRaises(ValueError):
                from_payload({**self.payload, 'records': records})

    def test_import_and_restore_accept_the_same_origins(self):
        self.assertEqual(ORIGINS, ('chrome', 'brave', 'firefox', 'unknown'))
        for source in ORIGINS:
            with self.subTest(source=source):
                self.assertEqual(ImportedFile(name='a.csv', source=source, credentials=[]).source, source)
                files = [dict(self.payload['files'][0], source=source)]
                self.assertEqual(from_payload({**self.payload, 'files': files})[1][0]['source'], source)
        files = [dict(self.payload['files'][0], source='edge')]
        with self.assertRaises(ValueError):
            ImportedFile(name='a.csv', source='edge', credentials=[])
        with self.assertRaises(ValueError):
            from_payload({**self.payload, 'files': files})

    def test_file_count_limit(self):
        files = [dict(self.payload['files'][0], name=f'{index}.csv') for index in range(16)]
        self.assertEqual(len(from_payload({**self.payload, 'files': files[:15]})[1]), 15)
        with self.assertRaises(ValueError):
            from_payload({**self.payload, 'files': files})

    def test_text_length_limit_in_original_and_edited_fields(self):
        for section in ('original', None):
            for length in (100_000, 100_001):
                with self.subTest(section=section, length=length):
                    payload = deepcopy(self.payload)
                    field = payload['records'][0][section] if section else payload['records'][0]
                    field['note'] = 'x' * length
                    if length == 100_000:
                        self.assertEqual(len(from_payload(payload)[0]), 1)
                    else:
                        with self.assertRaises(ValueError):
                            from_payload(payload)

    def test_file_name_length_limit_and_failed_restore_is_atomic(self):
        valid = deepcopy(self.payload)
        valid['files'][0]['name'] = 'x' * 1024
        self.assertEqual(len(from_payload(valid)[1]), 1)
        invalid = deepcopy(self.payload)
        invalid['files'][0]['name'] = 'x' * 1025
        with self.assertRaises(ValueError):
            self.workspace.restore(invalid)
        self.assertEqual(self.workspace.serialize(), self.payload)


if __name__ == '__main__':
    unittest.main()
