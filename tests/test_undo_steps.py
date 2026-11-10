"""Each undo step carries a description of what it changed (undo-ux S3). Synthetic data only."""
import sys
import threading
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
        self.assertNotEqual(second['id'], first['id'])
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
        seen = {before, self.last_change()['id']}
        self.assertEqual(len(seen), 2)
        payload = self.workspace.serialize()
        self.workspace.change(identifier, {'review': 'verified'})
        seen.add(self.last_change()['id'])
        self.workspace.restore(payload)
        self.assertIsNone(self.last_change())
        self.workspace.change(identifier, {'review': 'verified'})
        self.assertNotIn(self.last_change()['id'], seen)

    def test_concurrent_undos_of_the_same_step_undo_it_once(self):
        self.workspace.change(self.amazon, {'review': 'reviewed'})
        self.workspace.change(self.amazon, {'review': 'verified'})
        step, steps = self.last_change()['id'], len(self.workspace._history)
        start, results = threading.Barrier(16), []

        def undo():
            start.wait()
            try:
                self.workspace.undo(step)
                results.append(True)
            except ValueError:
                results.append(False)
        threads = [threading.Thread(target=undo) for _ in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(results.count(True), 1)
        self.assertEqual(len(self.workspace._history), steps - 1)

    def test_step_ids_are_never_repeated_not_even_after_a_server_restart(self):
        ids = []
        for workspace in (self.workspace, Workspace()):
            if not workspace._records:
                workspace._records = dict(self.workspace._records)
            for review in ('reviewed', 'verified', 'pending'):
                workspace.change(self.amazon, {'review': review})
                ids.append(workspace.snapshot()['last_change']['id'])
        self.assertTrue(all(isinstance(step, str) and step for step in ids))
        self.assertEqual(len(set(ids)), len(ids))

    def test_undo_of_a_step_that_is_no_longer_the_last_is_refused_and_changes_nothing(self):
        self.workspace.change(self.amazon, {'review': 'reviewed'})
        shown = self.last_change()
        # Another tab trashes a record: the step the first tab shows is no longer the last one.
        self.workspace.trash([self.netflix_old])
        before = self.workspace.snapshot()
        with self.assertRaises(ValueError):
            self.workspace.undo(shown['id'])
        self.assertEqual(self.workspace.snapshot(), before)
        undone = self.workspace.undo(before['last_change']['id'])
        self.assertEqual(undone['undone'], before['last_change'])
        self.assertEqual(self.workspace.undo(shown['id'])['undone'], shown)

    def test_a_save_that_also_moves_the_record_is_an_edit_that_names_the_trash(self):
        self.workspace.change(self.amazon, {'note': 'fictional-note', 'included': False})
        self.assertEqual(without_id(self.last_change()),
                         {'action': 'edit', 'count': 1, 'name': 'Amazon', 'fields': ['note', 'included']})

    def test_past_the_thirty_step_cap_each_undo_still_reports_its_own_step(self):
        ids = []
        for number in range(1, 32):
            self.workspace.change(self.amazon, {'name': f'Amazon {number}'})
            ids.append(self.last_change()['id'])
        self.assertEqual(len(self.workspace._history), 30)
        for number in range(31, 1, -1):
            undone = self.workspace.undo()
            self.assertEqual(undone['undone']['id'], ids[number - 1])
            self.assertEqual(undone['undone']['name'], f'Amazon {number}')
            name = next(r['name'] for r in undone['records'] if r['id'] == self.amazon)
            self.assertEqual(name, f'Amazon {number - 1}')
        self.assertIsNone(self.last_change())
        self.assertFalse(self.workspace.snapshot()['can_undo'])


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

    def test_undo_refuses_a_step_that_is_no_longer_the_last_one(self):
        csv = b'name,url,username,password,note\nSite,https://site.invalid/,alice,fictional-secret-123,\n'
        identifier = self.client.post('/api/import', files=[('files', ('chrome.csv', csv, 'text/csv'))]).json()['records'][0]['id']
        shown = self.client.patch('/api/records/' + identifier, json={'review': 'verified'}).json()['last_change']
        last = self.client.patch('/api/records/' + identifier, json={'note': 'fictional-note'}).json()['last_change']
        before = self.client.get('/api/workspace').json()
        refused = self.client.post('/api/undo', json={'step': shown['id']})
        self.assertEqual(refused.status_code, 409, refused.text)
        self.assertEqual(refused.json()['detail'], 'El último cambio ya no es el que se muestra en pantalla')
        self.assertEqual(self.client.get('/api/workspace').json(), before)
        self.assertEqual(self.client.post('/api/undo', json={'step': 'x', 'other': 1}).status_code, 422)
        accepted = self.client.post('/api/undo', json={'step': last['id']})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()['undone'], last)

    def test_undo_rejects_malformed_steps_and_names_an_empty_history(self):
        csv = b'name,url,username,password,note\nSite,https://site.invalid/,alice,fictional-secret-123,\n'
        identifier = self.client.post('/api/import', files=[('files', ('chrome.csv', csv, 'text/csv'))]).json()['records'][0]['id']
        step = self.client.patch('/api/records/' + identifier, json={'review': 'verified'}).json()['last_change']['id']
        for body in ({}, {'step': ''}, {'step': 'a' * 65}, {'step': 5}, {'step': None}, [step]):
            with self.subTest(body=body):
                before = self.client.get('/api/workspace').content
                response = self.client.post('/api/undo', json=body)
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(self.client.get('/api/workspace').content, before)
        self.assertEqual(self.client.post('/api/undo', json={'step': step}).status_code, 200)
        empty = self.client.post('/api/undo', json={'step': step})
        self.assertEqual(empty.status_code, 409, empty.text)
        self.assertEqual(empty.json()['detail'], 'No hay cambios que deshacer')


if __name__ == '__main__':
    unittest.main()
