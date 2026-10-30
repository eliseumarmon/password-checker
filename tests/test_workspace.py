"""Tests use synthetic records only. No real credentials or network calls."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.workspace import Workspace, detect_groups, detect_audit, Candidate
from auditar_contrasenas_local import Credential


def cred(name, url, user, password, source='chrome', note=''):
    return Credential(source, 2, name, url, user, password, note)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.workspace._records = {r.id: r for r in [
            Candidate.from_source(cred('GitHub', 'https://github.com/login', 'alice', 'fictional-one-123')),
            Candidate.from_source(cred('GitHub', 'https://github.com/login', 'alice', 'fictional-one-123', 'brave', 'second note')),
            Candidate.from_source(cred('GitHub', 'https://github.com/login', 'alice', 'fictional-two-456', 'firefox')),
            Candidate.from_source(cred('Other', 'https://other.invalid', 'bob', 'fictional-one-123')),
            Candidate.from_source(cred('VK app', 'android://SIGN@com.example.app/', 'eve', 'fictional-app-123')),
        ]}

    def test_initially_no_auto_merge_and_android_conversion(self):
        snapshot = self.workspace.snapshot()
        self.assertEqual(snapshot['stats']['included'], 5)
        self.assertEqual(snapshot['groups'][0]['kind'], 'conflict')
        self.assertEqual(snapshot['groups'][0]['count'], 3)
        self.assertEqual(snapshot['audit']['breaches'], 'not_checked')
        self.assertEqual(len(snapshot['audit']['reused']), 1)
        android = next(r for r in snapshot['records'] if r['type'] == 'android')
        self.assertEqual(android['url'], 'androidapp://com.example.app')

    def test_explicit_merge_undo_and_preserve_conflict(self):
        rows = self.workspace.snapshot()['records']
        self.workspace.merge_exact()
        snapshot = self.workspace.snapshot()
        self.assertEqual(snapshot['stats']['included'], 4)
        self.assertEqual(snapshot['stats']['excluded'], 1)
        exported, count = self.workspace.export_csv()
        self.assertEqual(count, 4)
        self.assertIn(b'fictional-two-456', exported)
        self.assertIn(b'second note', exported)
        self.workspace.undo()
        self.assertEqual(self.workspace.snapshot()['stats']['included'], 5)

    def test_verification_invalidated_by_password_edit_but_not_note(self):
        identifier = self.workspace.snapshot()['records'][0]['id']
        self.workspace.change(identifier, {'review': 'verified'})
        self.workspace.change(identifier, {'note': 'reviewed'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'verified')
        self.workspace.change(identifier, {'password': 'fictional-changed-123'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'pending')
        self.workspace.undo()
        self.assertEqual(self.workspace.get(identifier)['review'], 'verified')

    def test_explicit_review_in_the_same_edit_is_kept(self):
        identifier = self.workspace.snapshot()['records'][0]['id']
        self.workspace.change(identifier, {'password': 'fictional-new-123456', 'review': 'verified'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'verified')
        # The editor form resends the unchanged review: the edit still invalidates it.
        self.workspace.change(identifier, {'password': 'fictional-other-123456', 'review': 'verified'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'pending')

    def test_trash_many_is_atomic_and_one_undo_step(self):
        ids = [r['id'] for r in self.workspace.snapshot()['records'][:3]]
        with self.assertRaises(KeyError):
            self.workspace.trash(ids + ['missing'])
        self.assertEqual(self.workspace.snapshot()['stats']['excluded'], 0)
        self.assertEqual(self.workspace.trash(ids)['stats']['excluded'], 3)
        self.assertEqual(self.workspace.undo()['stats']['excluded'], 0)
        with self.assertRaises(ValueError):
            self.workspace.trash([])

    def test_exact_group_only_when_merge_exact_can_merge_it(self):
        self.workspace._records = {r.id: r for r in [
            Candidate.from_source(cred('A', 'https://a.invalid/', '', 'fictional-123456')) for _ in range(2)]}
        self.assertNotEqual(self.workspace.snapshot()['groups'][0]['kind'], 'exact')
        self.assertEqual(self.workspace.merge_exact()['stats']['excluded'], 0)

    def test_blank_name_falls_back_like_the_cli(self):
        record = Candidate.from_source(cred('   ', 'https://a.invalid/login', 'alice', 'fictional-123456'))
        self.assertEqual(record.name, 'a.invalid')

    def test_input_files_transactional(self):
        before = self.workspace.snapshot()['stats']['total']
        try:
            self.workspace.import_files([('good.csv', b'name,url,username,password,note\nA,https://example.org,u,fake-123,note\n'), ('bad.csv', b'\x00')])
        except ValueError:
            pass
        else:
            self.fail('Malformed import must fail')
        self.assertEqual(self.workspace.snapshot()['stats']['total'], before)

    def test_import_detects_firefox_without_name_hint(self):
        data = ('url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged\n'
                'https://example.org/login,alice,fictional-abc-123,,,,,,\n').encode()
        result = self.workspace.import_files([('passwords.csv', data)])
        self.assertEqual(result['files'][0]['source'], 'firefox')
        self.assertEqual(result['stats']['total'], 1)

    def test_partial_updates_cannot_change_id_or_original(self):
        identifier = self.workspace.snapshot()['records'][0]['id']
        for invalid in ({'id': 'evil'}, {'original': None}, {'review': 'arbitrary'}):
            with self.assertRaises(ValueError):
                self.workspace.change(identifier, invalid)


if __name__ == '__main__':
    unittest.main()
