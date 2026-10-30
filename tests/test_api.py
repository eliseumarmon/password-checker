"""HTTP contract tests with synthetic data; no production secrets."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from fastapi.testclient import TestClient
    from backend.password_checker.api import app, workspace
except ImportError:
    TestClient = None


@unittest.skipUnless(TestClient is not None, 'Optional API dependencies not installed')
class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url='http://127.0.0.1:8000')
        workspace._records.clear()
        workspace._history.clear()
        workspace._files.clear()

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

    def test_import_is_all_files_or_none(self):
        good = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        self.client.post('/api/import', files=[('files', ('chrome.csv', good, 'text/csv'))])
        two_rows = good + b'B,https://b.invalid/,bob,fictional-654321,\n'
        response = self.client.post('/api/import', files=[('files', ('chrome.csv', two_rows, 'text/csv')),
                                                          ('files', ('bad.csv', b'\x00', 'text/csv'))])
        self.assertEqual(response.status_code, 422)
        self.assertEqual(workspace.snapshot()['stats']['total'], 1)

    def test_trash_many_records_in_one_request(self):
        payload = (b'name,url,username,password,note\n'
                   b'A,https://a.invalid/,alice,fictional-123456,\n'
                   b'B,https://b.invalid/,bob,fictional-654321,\n')
        state = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))]).json()
        ids = [r['id'] for r in state['records']]
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': ids}).json()['stats']['excluded'], 2)
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': ['missing']}).status_code, 404)
        self.assertEqual(self.client.post('/api/records/trash', json={'ids': []}).status_code, 422)

    def test_save_and_restore_session(self):
        payload = b'name,url,username,password,note\nA,https://example.org/login,alice,fictional-123456,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))]).json()
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

    def test_cross_origin_rejected_and_no_cache(self):
        response = self.client.get('/api/workspace', headers={'Origin': 'https://evil.example'})
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/api/workspace')
        self.assertEqual(response.headers['cache-control'], 'no-store')


if __name__ == '__main__':
    unittest.main()
