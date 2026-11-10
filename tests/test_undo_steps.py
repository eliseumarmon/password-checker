"""Each undo step carries a description of what it changed (undo-ux S3). Synthetic data only."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from backend.password_checker.api import app
from backend.password_checker.api import workspace as api_workspace
from backend.password_checker.application.candidate import Candidate
from backend.password_checker.application.workspace import ImportedFile, Workspace
from backend.password_checker.domain.credential import Credential


def cred(name, url, user, password, source='chrome'):
    return Credential(source, 2, name, url, user, password, '')


def without_id(change):
    return {key: value for key, value in change.items() if key != 'id'}


class UndoStepTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        rows = [
            Candidate.from_source(cred('Netflix', 'https://netflix.invalid/login', 'ana', 'fictional-old-111')),
            Candidate.from_source(cred('Netflix', 'https://netflix.invalid/login', 'ana', 'fictional-new-222', 'firefox')),
            Candidate.from_source(cred('Amazon', 'https://amazon.invalid/', 'ana', 'fictional-card-333')),
            Candidate.from_source(cred('Amazon', 'https://amazon.invalid/', 'ana', 'fictional-card-333', 'brave')),
        ]
        self.workspace._records = {r.id: r for r in rows}
        self.netflix_old, self.netflix_new, self.amazon, self.amazon_copy = (r.id for r in rows)

    def last_change(self):
        return self.workspace.snapshot()['last_change']

    def test_nothing_to_describe_before_any_change(self):
        self.assertIsNone(self.last_change())

    def test_save_names_the_changed_fields_in_form_order_and_never_their_values(self):
        self.workspace.change(self.netflix_old, {'note': 'fictional-note-xyz', 'password': 'fictional-new-222',
                                                 'name': 'Netflix'})
        change = self.last_change()
        self.assertEqual(without_id(change), {'action': 'edit', 'count': 1, 'name': 'Netflix',
                                              'fields': ['password', 'note']})
        self.assertNotIn('fictional', repr(change))

    def test_save_lists_the_review_reset_that_a_new_secret_causes(self):
        self.workspace.change(self.netflix_old, {'review': 'verified'})
        self.workspace.change(self.netflix_old, {'password': 'fictional-new-222'})
        self.assertEqual(self.last_change()['fields'], ['password', 'review'])

    def test_save_of_a_renamed_record_uses_its_new_name(self):
        self.workspace.change(self.amazon, {'name': 'Amazon (tarjeta)'})
        self.assertEqual(without_id(self.last_change()),
                         {'action': 'edit', 'count': 1, 'name': 'Amazon (tarjeta)', 'fields': ['name']})

    def test_save_without_changes_keeps_the_previous_description(self):
        self.workspace.change(self.amazon, {'review': 'reviewed'})
        before = self.last_change()
        self.workspace.change(self.amazon, {'review': 'reviewed', 'note': ''})
        self.assertEqual(self.last_change(), before)

    def test_quick_trash_and_restore_are_described_as_such(self):
        self.workspace.change(self.amazon, {'included': False})
        self.assertEqual(without_id(self.last_change()),
                         {'action': 'trash', 'count': 1, 'name': 'Amazon', 'fields': []})
        self.workspace.change(self.amazon, {'included': True})
        self.assertEqual(without_id(self.last_change()),
                         {'action': 'restore', 'count': 1, 'name': 'Amazon', 'fields': []})

    def test_trashing_several_records_counts_only_the_moved_ones_and_names_a_shared_name(self):
        self.workspace.change(self.netflix_old, {'included': False})
        self.workspace.trash([self.netflix_old, self.netflix_new, self.netflix_new])
        self.assertEqual(without_id(self.last_change()),
                         {'action': 'trash', 'count': 1, 'name': 'Netflix', 'fields': []})
        self.workspace.trash([self.amazon, self.amazon_copy])
        self.assertEqual(self.last_change()['count'], 2)
        self.assertEqual(self.last_change()['name'], 'Amazon')

    def test_trashing_records_with_different_names_has_no_shared_name(self):
        self.workspace.trash([self.netflix_old, self.amazon])
        self.assertEqual(without_id(self.last_change()),
                         {'action': 'trash', 'count': 2, 'name': None, 'fields': []})

    def test_merge_counts_the_copies_it_moves_to_the_trash(self):
        self.workspace.merge_exact()
        self.assertEqual(without_id(self.last_change()),
                         {'action': 'merge', 'count': 1, 'name': 'Amazon', 'fields': []})

    def test_undo_reports_what_it_undid_and_exposes_the_step_below(self):
        self.workspace.change(self.amazon, {'review': 'reviewed'})
        first = self.last_change()
        self.workspace.trash([self.netflix_old])
        second = self.last_change()
        self.assertGreater(second['id'], first['id'])
        undone = self.workspace.undo()
        self.assertEqual(undone['undone'], second)
        self.assertEqual(undone['last_change'], first)
        self.assertNotIn('undone', self.workspace.snapshot())
        last = self.workspace.undo()
        self.assertEqual(last['undone'], first)
        self.assertIsNone(last['last_change'])
        self.assertFalse(last['can_undo'])

    def test_import_and_opening_a_session_clear_the_description_but_never_reuse_an_id(self):
        self.workspace.change(self.amazon, {'review': 'reviewed'})
        before = self.last_change()['id']
        self.workspace.import_files([ImportedFile(name='chrome.csv', source='chrome', credentials=[
            cred('GitHub', 'https://github.invalid/', 'ana', 'fictional-git-444')])])
        self.assertIsNone(self.last_change())
        identifier = next(iter(self.workspace._records))
        self.workspace.change(identifier, {'review': 'reviewed'})
        self.assertGreater(self.last_change()['id'], before)
        payload = self.workspace.serialize()
        self.workspace.change(identifier, {'review': 'verified'})
        self.workspace.restore(payload)
        self.assertIsNone(self.last_change())


class UndoStepAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url='http://127.0.0.1:8000')
        api_workspace._records.clear()
        api_workspace._history.clear()
        api_workspace._files.clear()

    def test_the_workspace_describes_the_last_step_and_undo_reports_the_undone_one(self):
        csv = b'name,url,username,password,note\nSite,https://site.invalid/,alice,fictional-secret-123,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', csv, 'text/csv'))]).json()
        self.assertIsNone(imported['last_change'])
        identifier = imported['records'][0]['id']
        edited = self.client.patch('/api/records/' + identifier, json={'review': 'verified'}).json()
        change = edited['last_change']
        self.assertEqual(without_id(change), {'action': 'edit', 'count': 1, 'name': 'Site', 'fields': ['review']})
        self.assertEqual(self.client.get('/api/workspace').json()['last_change'], change)
        undone = self.client.post('/api/undo')
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertEqual(undone.json()['undone'], change)
        self.assertIsNone(undone.json()['last_change'])
        self.assertNotIn('undone', self.client.get('/api/workspace').json())


if __name__ == '__main__':
    unittest.main()
