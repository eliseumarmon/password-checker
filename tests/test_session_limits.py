"""Every accepted operation keeps the workspace savable and restorable. Fabricated values only."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.application import limits
from backend.password_checker.application.session_snapshot import encode_payload
from backend.password_checker.application.workspace import ImportedFile, Workspace
from backend.password_checker.domain.credential import Credential

try:
    from backend.password_checker.infrastructure.sessions import encrypt_session
except ImportError:
    encrypt_session = None

PASSPHRASE = 'fictional-passphrase-123'


def cred(line, name='Site', url='https://site.invalid/', user='user', password='fictional-pass-123', note=''):
    return Credential('chrome', line, name, url, user, password, note)


def imported(*credentials, name='chrome.csv'):
    return ImportedFile(name=name, source='chrome', credentials=credentials)


class WorkspaceSessionLimitTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.workspace.import_files([imported(cred(2, note='first'), cred(3, url='https://other.invalid/'))])
        self.before = self.workspace.snapshot()

    def plaintext_size(self):
        return len(encode_payload(self.workspace.serialize()))

    def assert_unchanged(self):
        self.assertEqual(self.workspace.snapshot(), self.before)

    def test_import_over_record_limit_is_rejected_and_keeps_workspace(self):
        with patch.object(limits, 'MAX_SESSION_RECORDS', 2), self.assertRaisesRegex(ValueError, 'como máximo 2 credenciales'):
            self.workspace.import_files([imported(cred(2), cred(3), cred(4))])
        self.assert_unchanged()

    def test_import_with_field_over_text_limit_names_the_field_not_the_value(self):
        secret = 'fictional-secret-note-' + 'x' * 30
        with patch.object(limits, 'MAX_SNAPSHOT_TEXT_CHARS', 20), self.assertRaises(ValueError) as caught:
            self.workspace.import_files([imported(cred(7, name='Ok', url='https://a.invalid', user='u',
                                                       password='p', note=secret))])
        message = str(caught.exception)
        self.assertIn('«notas»', message)
        self.assertIn('línea 7', message)
        self.assertNotIn(secret, message)
        self.assert_unchanged()

    def test_import_that_would_not_fit_in_a_session_file_is_rejected(self):
        many = [cred(line, url=f'https://site-{line}.invalid/') for line in range(2, 60)]
        with patch.object(limits, 'MAX_SESSION_BYTES', 4096), self.assertRaisesRegex(ValueError, 'no cabe en una sesión cifrada'):
            self.workspace.import_files([imported(*many)])
        self.assert_unchanged()

    def test_edit_that_would_not_fit_is_rejected_without_an_undo_step(self):
        record_id = self.before['records'][0]['id']
        limit = limits.session_file_size(self.plaintext_size() + 10)
        with patch.object(limits, 'MAX_SESSION_BYTES', limit), self.assertRaisesRegex(ValueError, 'no cabe en una sesión cifrada'):
            self.workspace.change(record_id, {'note': 'y' * 200})
        self.assert_unchanged()

    def test_trash_that_would_not_fit_is_rejected(self):
        # Moving a record to the trash turns "true" into "false": one byte more.
        record_id = self.before['records'][0]['id']
        with patch.object(limits, 'MAX_SESSION_BYTES', limits.session_file_size(self.plaintext_size())):
            while limits.session_file_size(self.plaintext_size() + 1) <= limits.MAX_SESSION_BYTES:
                self.workspace.change(record_id, {'note': self.workspace.get(record_id)['note'] + 'z'})
            self.before = self.workspace.snapshot()
            with self.assertRaisesRegex(ValueError, 'no cabe en una sesión cifrada'):
                self.workspace.trash([record_id])
        self.assert_unchanged()

    def test_merge_that_would_exceed_the_text_limit_is_rejected(self):
        self.workspace.import_files([imported(cred(2, note='fictional note one'), cred(3, note='fictional note two'))])
        self.before = self.workspace.snapshot()
        with patch.object(limits, 'MAX_SNAPSHOT_TEXT_CHARS', 30), self.assertRaisesRegex(ValueError, '«notas»'):
            self.workspace.merge_exact()
        self.assert_unchanged()

    def test_operations_that_reduce_an_existing_excess_are_allowed(self):
        record_id = self.before['records'][0]['id']
        self.workspace.change(record_id, {'note': 'w' * 300})
        with patch.object(limits, 'MAX_SESSION_BYTES', limits.session_file_size(self.plaintext_size() - 100)):
            snapshot = self.workspace.change(record_id, {'note': 'w' * 250})
            self.assertTrue(snapshot['can_undo'])
            self.assertEqual(self.workspace.get(record_id)['note'], 'w' * 250)
            with self.assertRaisesRegex(ValueError, 'no cabe en una sesión cifrada'):
                self.workspace.change(record_id, {'note': 'w' * 260})
        self.assertEqual(self.workspace.get(record_id)['note'], 'w' * 250)

    def test_operations_that_do_not_touch_the_exceeded_limit_are_allowed(self):
        record_id = self.before['records'][0]['id']
        other_id = self.before['records'][1]['id']
        self.workspace.change(record_id, {'note': 'v' * 40})
        with patch.object(limits, 'MAX_SNAPSHOT_TEXT_CHARS', 30):
            # Over the text limit only: one byte more for the trash or the other record is fine.
            self.workspace.trash([other_id])
            self.workspace.change(other_id, {'name': 'Site renamed'})
            with self.assertRaisesRegex(ValueError, '«notas»'):
                self.workspace.change(other_id, {'note': 'u' * 40})
        self.assertEqual(self.workspace.get(other_id)['name'], 'Site renamed')

    def test_restore_rejects_a_session_that_could_not_be_saved_again(self):
        payload = self.workspace.serialize()
        with patch.object(limits, 'MAX_SESSION_BYTES', 1024):
            with self.assertRaisesRegex(ValueError, 'no cabe en una sesión cifrada'):
                Workspace().restore(payload)
            with self.assertRaisesRegex(ValueError, 'no cabe en una sesión cifrada'):
                self.workspace.restore(payload)
        self.assert_unchanged()
        restored = Workspace()
        restored.restore(payload)
        self.assertEqual(restored.snapshot()['records'], self.before['records'])

    def test_saving_validates_the_state_defensively(self):
        with patch.object(limits, 'MAX_SESSION_RECORDS', 1), self.assertRaisesRegex(ValueError, 'Número de credenciales no válido'):
            self.workspace.serialize()


@unittest.skipUnless(encrypt_session is not None, 'Optional cryptography dependencies not installed')
class SessionFileSizeTests(unittest.TestCase):
    def test_computed_size_matches_the_real_file(self):
        for pad in range(6):
            payload = {'version': 1, 'files': [], 'records': [], 'pad': 'x' * pad}
            real = len(encrypt_session(payload, PASSPHRASE))
            self.assertEqual(limits.session_file_size(len(encode_payload(payload))), real)

    def test_encrypt_refuses_a_file_over_the_limit(self):
        payload = {'version': 1, 'files': [], 'records': [], 'pad': 'x' * 100}
        size = len(encrypt_session(payload, PASSPHRASE))
        with patch.object(limits, 'MAX_SESSION_BYTES', size - 1), self.assertRaisesRegex(ValueError, 'no se ha generado el archivo'):
            encrypt_session(payload, PASSPHRASE)
        with patch.object(limits, 'MAX_SESSION_BYTES', size):
            self.assertEqual(len(encrypt_session(payload, PASSPHRASE)), size)


if __name__ == '__main__':
    unittest.main()
