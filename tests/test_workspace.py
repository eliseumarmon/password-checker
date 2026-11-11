"""Tests use synthetic records only. No real credentials or network calls."""
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.application.candidate import Candidate
from backend.password_checker.application.limits import MAX_SNAPSHOT_FILE_NAME_CHARS
from backend.password_checker.application.workspace import ImportedFile, Workspace
from backend.password_checker.domain.credential import Credential
from backend.password_checker.infrastructure.bitwarden import bitwarden_csv_bytes


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
        self.workspace.merge_exact()
        snapshot = self.workspace.snapshot()
        self.assertEqual(snapshot['stats']['included'], 4)
        self.assertEqual(snapshot['stats']['excluded'], 1)
        exported, count = bitwarden_csv_bytes(self.workspace.export_records())
        self.assertEqual(count, 4)
        self.assertIn(b'fictional-two-456', exported)
        self.assertIn(b'second note', exported)
        self.workspace.undo()
        self.assertEqual(self.workspace.snapshot()['stats']['included'], 5)

    def test_verification_invalidated_by_password_edit_but_not_note(self):
        identifier = self.workspace.snapshot()['records'][0]['id']
        self.workspace.change(identifier, {'review': 'reviewed'})
        self.workspace.change(identifier, {'note': 'reviewed'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'reviewed')
        self.workspace.change(identifier, {'password': 'fictional-changed-123'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'pending')
        self.workspace.undo()
        self.assertEqual(self.workspace.get(identifier)['review'], 'reviewed')

    def test_identity_edit_resets_review_even_when_set_in_the_same_edit(self):
        identifier = self.workspace.snapshot()['records'][0]['id']
        for field, value in (('password', 'fictional-new-123456'), ('username', 'carol'), ('url', 'https://new.invalid')):
            self.workspace.change(identifier, {field: value, 'review': 'reviewed'})
            self.assertEqual(self.workspace.get(identifier)['review'], 'pending', field)
        # Without an identity change, an explicit review state is kept.
        self.workspace.change(identifier, {'note': 'checked', 'review': 'reviewed'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'reviewed')

    def test_review_states_are_pending_reviewed_and_incorrect(self):
        identifier = self.workspace.snapshot()['records'][0]['id']
        for review in ('reviewed', 'incorrect', 'pending'):
            self.workspace.change(identifier, {'review': review})
            self.assertEqual(self.workspace.get(identifier)['review'], review)
        with self.assertRaises(ValueError):
            self.workspace.change(identifier, {'review': 'verified'})
        self.assertEqual(self.workspace.get(identifier)['review'], 'pending')
        self.assertNotIn('verified', self.workspace.snapshot()['stats'])

    def test_progress_counts_reviewed_and_trashed_records_but_not_incorrect_ones(self):
        ids = [r['id'] for r in self.workspace.snapshot()['records']]
        self.workspace.change(ids[0], {'review': 'reviewed'})
        self.workspace.change(ids[1], {'review': 'incorrect'})
        self.assertEqual(self.workspace.snapshot()['stats']['reviewed'], 1)
        # A trashed record counts whatever its state, also one still pending.
        stats = self.workspace.trash([ids[1], ids[2]])['stats']
        self.assertEqual((stats['reviewed'], stats['total']), (3, 5))
        stats = self.workspace.trash([ids[3], ids[4]])['stats']
        self.assertEqual((stats['reviewed'], stats['total']), (5, 5))
        stats = self.workspace.undo()['stats']
        self.assertEqual((stats['reviewed'], stats['total']), (3, 5))

    def test_a_multiple_accounts_group_is_resolved_once_every_active_member_is_reviewed(self):
        workspace = Workspace()
        workspace._records = {r.id: r for r in [
            Candidate.from_source(cred('Site', 'https://site.invalid/', user, f'fictional-{user}-123'))
            for user in ('ana', 'bob', 'eva')]}
        ana, bob, eva = workspace._records
        kinds = lambda snapshot: [(g['kind'], g['count']) for g in snapshot['groups']]
        workspace.change(ana, {'review': 'reviewed'})
        self.assertEqual(kinds(workspace.change(bob, {'review': 'incorrect'})), [('multiple-accounts', 3)])
        # A pending member keeps the group open even when the rest are reviewed.
        workspace.change(bob, {'review': 'reviewed'})
        self.assertEqual(kinds(workspace.snapshot()), [('multiple-accounts', 3)])
        self.assertEqual(kinds(workspace.change(eva, {'review': 'reviewed'})), [])
        self.assertEqual(kinds(workspace.undo()), [('multiple-accounts', 3)])
        # A trashed member no longer counts: the active ones decide.
        self.assertEqual(kinds(workspace.trash([eva])), [])

    def test_conflicting_and_exact_groups_stay_until_one_copy_is_left_however_reviewed(self):
        for record in self.workspace.snapshot()['records']:
            self.workspace.change(record['id'], {'review': 'reviewed'})
        self.assertEqual([g['kind'] for g in self.workspace.snapshot()['groups']], ['conflict'])

    def test_trash_many_is_atomic_and_one_undo_step(self):
        ids = [r['id'] for r in self.workspace.snapshot()['records'][:3]]
        with self.assertRaises(KeyError):
            self.workspace.trash(ids + ['missing'])
        self.assertEqual(self.workspace.snapshot()['stats']['excluded'], 0)
        self.assertEqual(self.workspace.trash(ids)['stats']['excluded'], 3)
        self.assertEqual(self.workspace.undo()['stats']['excluded'], 0)
        with self.assertRaises(ValueError):
            self.workspace.trash([])

    def test_trash_of_records_already_in_the_trash_adds_no_undo_step(self):
        ids = [r['id'] for r in self.workspace.snapshot()['records'][:3]]
        self.workspace.trash(ids[:2])
        self.assertEqual(self.workspace.trash(ids[:2] + ids[:2])['stats']['excluded'], 2)
        # Mixed batch: one already trashed, one repeated, one new; one undo step for the new one.
        self.assertEqual(self.workspace.trash([ids[1], ids[2], ids[2]])['stats']['excluded'], 3)
        self.assertEqual(self.workspace.undo()['stats']['excluded'], 2)
        # The redundant call added no step: the next undo restores the first trash.
        state = self.workspace.undo()
        self.assertEqual(state['stats']['excluded'], 0)
        self.assertFalse(state['can_undo'])

    def test_exact_group_only_when_merge_exact_can_merge_it(self):
        self.workspace._records = {r.id: r for r in [
            Candidate.from_source(cred('A', 'https://a.invalid/', '', 'fictional-123456')) for _ in range(2)]}
        self.assertNotEqual(self.workspace.snapshot()['groups'][0]['kind'], 'exact')
        self.assertEqual(self.workspace.merge_exact()['stats']['excluded'], 0)

    def test_blank_name_falls_back_to_site(self):
        record = Candidate.from_source(cred('   ', 'https://a.invalid/login', 'alice', 'fictional-123456'))
        self.assertEqual(record.name, 'a.invalid')

    def test_import_replaces_records_and_keeps_file_metadata(self):
        self.workspace.merge_exact()
        result = self.workspace.import_files([ImportedFile(name='passwords.csv', source='firefox', credentials=[cred('A', 'https://a.invalid', 'u', 'fake-123')])])
        self.assertEqual(result['files'], [{'name': 'passwords.csv', 'source': 'firefox', 'count': 1}])
        self.assertEqual(result['stats']['total'], 1)
        self.assertFalse(result['can_undo'])
        with self.assertRaises(ValueError):
            self.workspace.import_files([ImportedFile(name='empty.csv', source='chrome', credentials=[])])

    def test_imported_file_is_complete_immutable_and_validates_name(self):
        rows = [cred('A', 'https://a.invalid', 'u', 'fake-123')]
        file = ImportedFile(name=' passwords.csv ', source='chrome', credentials=rows)
        rows.clear()
        self.assertEqual(file.name, ' passwords.csv ')
        self.assertEqual(len(file.credentials), 1)
        with self.assertRaises(FrozenInstanceError):
            file.name = 'dir/passwords.csv'
        with self.assertRaises(TypeError):
            ImportedFile('passwords.csv', 'chrome', [])
        with self.assertRaises(TypeError):
            ImportedFile(name='passwords.csv')
        with self.assertRaises(ValueError):
            ImportedFile(name='passwords.csv', source='', credentials=[])
        for name in ('', '  ', '.', '..', 'dir/passwords.csv', r'dir\passwords.csv',
                     'bad\x00.csv', 'bad\x7f.csv', 'bad\x85.csv',
                     'x' * (MAX_SNAPSHOT_FILE_NAME_CHARS + 1)):
            with self.subTest(name=name), self.assertRaises(ValueError):
                ImportedFile(name=name, source='chrome', credentials=[])
        longest = 'x' * MAX_SNAPSHOT_FILE_NAME_CHARS
        self.assertEqual(ImportedFile(name=longest, source='chrome', credentials=[]).name, longest)

    def test_partial_updates_cannot_change_id_or_original(self):
        identifier = self.workspace.snapshot()['records'][0]['id']
        for invalid in ({'id': 'evil'}, {'original': None}, {'review': 'arbitrary'}):
            with self.assertRaises(ValueError):
                self.workspace.change(identifier, invalid)


if __name__ == '__main__':
    unittest.main()
