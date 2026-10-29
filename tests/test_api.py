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

    def test_cross_origin_rejected_and_no_cache(self):
        response = self.client.get('/api/workspace', headers={'Origin': 'https://evil.example'})
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/api/workspace')
        self.assertEqual(response.headers['cache-control'], 'no-store')


if __name__ == '__main__':
    unittest.main()
