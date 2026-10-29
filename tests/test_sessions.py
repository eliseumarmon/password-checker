"""Tests for encrypted, authenticated session files. All values are fabricated."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    from backend.password_checker.sessions import encrypt_session, decrypt_session
    from backend.password_checker.workspace import Workspace, Candidate
    from auditar_contrasenas_local import Credential
except ImportError:
    encrypt_session = None


@unittest.skipUnless(encrypt_session is not None, 'Optional cryptography dependencies not installed')
class SessionTests(unittest.TestCase):
    def setUp(self):
        self.password = 'correct-horse-fake-staple-7654'
        self.workspace = Workspace()
        original = Credential('firefox', 2, 'Example', 'https://example.org/login',
                              'user', 'fictional-secret-987654', 'fictional note')
        record = Candidate.from_source(original)
        self.workspace._records[record.id] = record
        self.workspace._files = [{'name': 'example.csv', 'source': 'firefox', 'count': 1}]
        self.record_id = record.id

    def test_roundtrip_preserves_verification_and_edited_notes(self):
        self.workspace.change(self.record_id, {'note': 'updated note', 'review': 'verified'})
        encrypted = encrypt_session(self.workspace.serialize(), self.password)
        self.assertNotIn(b'fictional-secret-987654', encrypted)
        restored = Workspace()
        snapshot = restored.restore(decrypt_session(encrypted, self.password))
        self.assertEqual(snapshot['stats']['verified'], 1)
        self.assertEqual(restored.get(self.record_id)['note'], 'updated note')
        self.assertEqual(restored.get(self.record_id)['password'], 'fictional-secret-987654')

    def test_wrong_password_and_tamper_dont_modify_workspace(self):
        encrypted = encrypt_session(self.workspace.serialize(), self.password)
        with self.assertRaises(ValueError):
            decrypt_session(encrypted, 'incorrect-long-fake-password')
        envelope = json.loads(encrypted)
        raw = list(envelope['data'])
        raw[2] = 'A' if raw[2] != 'A' else 'B'
        envelope['data'] = ''.join(raw)
        with self.assertRaises(ValueError):
            decrypt_session(json.dumps(envelope).encode(), self.password)
        self.assertEqual(self.workspace.snapshot()['stats']['total'], 1)

    def test_validation_prevents_partial_restore(self):
        invalid = self.workspace.serialize()
        invalid['records'][0]['review'] = ['verified']
        with self.assertRaises(ValueError):
            self.workspace.restore(invalid)
        self.assertEqual(self.workspace.get(self.record_id)['review'], 'pending')


if __name__ == '__main__':
    unittest.main()
