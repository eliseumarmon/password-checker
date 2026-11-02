"""HTTP contract tests with synthetic data; no production secrets."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
    from backend.password_checker.api import app, workspace
    from backend.password_checker.application import limits
except ImportError:
    TestClient = None

EXACT_COPIES_CSV = (b'name,url,username,password,note\n'
                    b'Site,https://site.invalid/,alice,fictional-secret-123,fictional note one\n'
                    b'Site,https://site.invalid/,alice,fictional-secret-123,fictional note two\n')


@unittest.skipUnless(TestClient is not None, 'Optional API dependencies not installed')
class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url='http://127.0.0.1:8000')
        workspace._records.clear()
        workspace._history.clear()
        workspace._files.clear()

    def import_exact_copies(self):
        response = self.client.post('/api/import', files=[('files', ('chrome.csv', EXACT_COPIES_CSV, 'text/csv'))])
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_save_refuses_a_session_that_could_not_be_opened_again(self):
        before = self.import_exact_copies()
        with patch.object(limits, 'MAX_SESSION_RECORDS', 1):
            response = self.client.post('/api/session/save', json={'passphrase': 'fictional-passphrase-123'})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('content-disposition', response.headers)
        self.assertNotIn('fictional-secret-123', response.text)
        self.assertEqual(self.client.get('/api/workspace').json(), before)

    def test_rejected_merge_and_trash_are_client_errors_that_change_nothing(self):
        before = self.import_exact_copies()
        with patch.object(limits, 'MAX_SNAPSHOT_TEXT_CHARS', 30):
            merged = self.client.post('/api/merge-exact')
        self.assertEqual(merged.status_code, 422)
        self.assertIn('«notas»', merged.json()['detail'])
        with patch.object(limits, 'MAX_SESSION_BYTES', 64):
            trashed = self.client.post('/api/records/trash', json={'ids': [before['records'][0]['id']]})
        self.assertEqual(trashed.status_code, 422)
        self.assertNotIn('fictional-secret-123', merged.text + trashed.text)
        self.assertEqual(self.client.get('/api/workspace').json(), before)

    def test_import_edit_export_and_security(self):
        fake_csv = (b'name,url,username,password,note\n'
                    b'GitHub,https://github.com/login,alice,fictional-secret-123,\n'
                    b'GitHub,https://github.com/login,alice,fictional-secret-123,\n')
        response = self.client.post('/api/import', files=[('files', ('chrome.csv', fake_csv, 'text/csv'))])
        self.assertEqual(response.status_code, 200, response.text)
        state = response.json()
        self.assertEqual(state['stats']['total'], 2)
        self.assertEqual(state['groups'][0]['kind'], 'exact')
        self.assertNotIn('fictional-secret-123', response.text)
        identifier = state['records'][0]['id']
        detail = self.client.get('/api/records/' + identifier)
        self.assertEqual(detail.json()['password'], 'fictional-secret-123')
        self.assertEqual(self.client.patch('/api/records/' + identifier, json={'password': None}).status_code, 422)
        self.assertEqual(self.client.patch('/api/records/' + identifier, json={'original': {'password': 'other'}}).status_code, 422)
        self.assertEqual(self.client.post('/api/merge-exact').json()['stats']['included'], 1)
        export = self.client.get('/api/export')
        self.assertEqual(export.status_code, 200)
        self.assertIn('filename="bitwarden_import.csv"', export.headers['content-disposition'])
        self.assertIn(b'fictional-secret-123', export.content)
        self.assertEqual(self.client.post('/api/undo').json()['stats']['included'], 2)

    def test_import_uses_base_name_for_source_and_metadata(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        response = self.client.post('/api/import', files=[
            ('files', ('brave/passwords.csv', payload, 'text/csv')),
            ('files', ('dir/Brave Passwords.csv', payload, 'text/csv')),
            ('files', (r'brave\passwords.csv', payload, 'text/csv')),
            ('files', (r'dir/subdir\Brave Passwords.csv', payload, 'text/csv')),
        ])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['files'], [
            {'name': 'passwords.csv', 'source': 'unknown', 'count': 1},
            {'name': 'Brave Passwords.csv', 'source': 'brave', 'count': 1},
            {'name': 'passwords.csv', 'source': 'unknown', 'count': 1},
            {'name': 'Brave Passwords.csv', 'source': 'brave', 'count': 1},
        ])

    def test_import_rejects_name_too_long_for_session_metadata(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        accepted_name = 'x' * 1020 + '.csv'
        accepted = self.client.post('/api/import', files=[('files', (accepted_name, payload, 'text/csv'))])
        self.assertEqual(accepted.status_code, 200, accepted.text)
        before = workspace.snapshot()
        rejected = self.client.post('/api/import', files=[('files', ('x' + accepted_name, payload, 'text/csv'))])
        self.assertEqual(rejected.status_code, 422, rejected.text)
        self.assertEqual(workspace.snapshot(), before)

    def test_import_is_all_files_or_none(self):
        good = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        self.client.post('/api/import', files=[('files', ('chrome.csv', good, 'text/csv'))])
        two_rows = good + b'B,https://b.invalid/,bob,fictional-654321,\n'
        response = self.client.post('/api/import', files=[('files', ('chrome.csv', two_rows, 'text/csv')),
                                                          ('files', ('bad.csv', b'\x00', 'text/csv'))])
        self.assertEqual(response.status_code, 422)
        self.assertEqual(workspace.snapshot()['stats']['total'], 1)

    def test_csv_with_bad_quoting_is_a_422_that_changes_nothing(self):
        good = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', good, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        before = workspace.snapshot()
        bad = b'name,url,username,password,note\nB,https://b.invalid/,bob,"fictional-secret-555"x,\n'
        response = self.client.post('/api/import', files=[('files', ('valid.csv', good, 'text/csv')),
                                                          ('files', ('chrome.csv', bad, 'text/csv'))])
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn('formato no válido', response.json()['detail'])
        self.assertNotIn('fictional-secret-555', response.text)
        self.assertEqual(workspace.snapshot(), before)

    def test_malformed_csv_rejected_without_exposing_secret_or_changing_workspace(self):
        good = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', good, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        before = workspace.snapshot()
        malformed = (b'name,url,username,password,note\n'
                     b'B,https://b.invalid/,bob,fictional-secret-987,note,extra\n')
        response = self.client.post('/api/import', files=[('files', ('chrome.csv', malformed, 'text/csv'))])
        self.assertEqual(response.status_code, 422, response.text)
        self.assertNotIn('fictional-secret-987', response.text)
        self.assertEqual(workspace.snapshot(), before)

    def test_import_file_count_limit_matches_session_metadata(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        files = [('files', (f'{index}.csv', payload, 'text/csv')) for index in range(16)]
        accepted = self.client.post('/api/import', files=files[:15])
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(len(accepted.json()['files']), 15)
        rejected = self.client.post('/api/import', files=files)
        self.assertEqual(rejected.status_code, 400, rejected.text)
        self.assertEqual(rejected.json()['detail'], 'Selecciona entre 1 y 15 archivos')
        self.assertEqual(len(workspace.snapshot()['files']), 15)

    def test_trash_many_records_in_one_request(self):
        payload = (b'name,url,username,password,note\n'
                   b'A,https://a.invalid/,alice,fictional-123456,\n'
                   b'B,https://b.invalid/,bob,fictional-654321,\n')
        state = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))]).json()
        ids = [r['id'] for r in state['records']]
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': ids}).json()['stats']['excluded'], 2)
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': ['missing']}).status_code, 404)
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': []}).status_code, 422)

    def test_trash_request_id_count_boundary(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        identifier = imported.json()['records'][0]['id']
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': []}).status_code, 422)
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': [identifier] * 1001}).status_code, 422)
        self.assertEqual(workspace.snapshot()['stats']['excluded'], 0)
        accepted = self.client.post('/api/records/trash', json={'ids': [identifier] * 1000})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()['stats']['excluded'], 1)

    def test_save_and_restore_session(self):
        payload = b'name,url,username,password,note\nA,https://example.org/login,alice,fictional-123456,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))]).json()
        self.assertNotIn('session_saved', imported)
        self.assertNotIn('session_saved', self.client.get('/api/workspace').json())
        identifier = imported['records'][0]['id']
        self.client.patch('/api/records/' + identifier, json={'review': 'verified'})
        passphrase = 'fictional-session-passphrase-12345'
        saved = self.client.post('/api/session/save', json={'passphrase': passphrase})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertNotIn(b'fictional-123456', saved.content)
        # Failing to decrypt must preserve current workspace.
        invalid = self.client.post('/api/session/load', data={'passphrase': 'wrong-long-passphrase'},
                                   files={'file': ('session.pwc', saved.content, 'application/octet-stream')})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(workspace.snapshot()['stats']['verified'], 1)
        self.client.patch('/api/records/' + identifier, json={'review': 'pending'})
        restored = self.client.post('/api/session/load', data={'passphrase': passphrase},
                                    files={'file': ('session.pwc', saved.content, 'application/octet-stream')})
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertEqual(restored.json()['stats']['verified'], 1)
        self.assertNotIn('session_saved', restored.json())
        self.assertNotIn('session_saved', self.client.get('/api/workspace').json())

    def test_session_passphrase_length_boundary(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        self.assertEqual(self.client.post('/api/session/save', json={'passphrase': 'x' * 11}).status_code, 422)
        accepted = self.client.post('/api/session/save', json={'passphrase': 'x' * 12})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(self.client.post('/api/session/save', json={'passphrase': 'x' * 1025}).status_code, 422)

    def test_cross_origin_rejected_and_no_cache(self):
        response = self.client.get('/api/workspace', headers={'Origin': 'https://evil.example'})
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/api/workspace')
        self.assertEqual(response.headers['cache-control'], 'no-store')


if __name__ == '__main__':
    unittest.main()
