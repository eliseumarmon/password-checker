"""Workspace observable contract (export bytes, merged notes, audit); synthetic records only."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.domain.credential import Credential  # noqa: E402
from backend.password_checker.workspace import Candidate, Workspace, detect_audit  # noqa: E402

SEPARATOR = '\n\n----- Nota adicional -----\n\n'


def candidate(url, user, password, note='', name='Site', source='chrome'):
    return Candidate.from_source(Credential(source, 2, name, url, user, password, note))


def workspace_with(*rows):
    workspace = Workspace()
    workspace._records = {r.id: r for r in rows}
    return workspace


class WorkspaceContractTests(unittest.TestCase):
    def test_export_bytes_use_bom_lf_and_bitwarden_columns(self):
        exported, count = workspace_with(candidate('https://a.invalid', 'u', 'fake,pw', 'n', 'Site')).export_csv()
        self.assertEqual(count, 1)
        self.assertEqual(exported, (
            '﻿folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password,login_totp\n'
            ',,login,Site,n,,0,https://a.invalid,u,"fake,pw",\n').encode('utf-8'))

    def test_android_candidate_follows_bitwarden_chrome_importer(self):
        app = candidate('android://SIGN@Com.Example.App/', 'eve', 'fake-app-123456', 'mine', name='')
        self.assertEqual((app.url, app.name, app.note), ('androidapp://Com.Example.App', 'Com.Example.App', 'mine'))
        self.assertEqual(app.original.url, 'android://SIGN@Com.Example.App/')

    def test_merge_keeps_distinct_non_blank_notes_in_order(self):
        rows = [candidate('https://a.invalid', 'u', 'fake-1234567890', note) for note in ('first', ' ', 'second', 'first')]
        workspace = workspace_with(*rows)
        workspace.merge_exact()
        self.assertEqual(workspace.get(rows[0].id)['note'], 'first' + SEPARATOR + 'second')
        self.assertEqual([workspace.get(r.id)['included'] for r in rows], [True, False, False, False])

    def test_audit_weak_ignores_empty_passwords_and_groups_reuse_by_account(self):
        empty = candidate('https://e.invalid', 'u', '')
        short = candidate('https://s.invalid', 'u', 'fake-123')
        shared_a = candidate('https://a.invalid', 'alice', 'fake-shared-123456')
        shared_b = candidate('https://b.invalid', 'alice', 'fake-shared-123456')
        same_account = candidate('https://a.invalid', 'alice', 'fake-shared-123456', source='brave')
        audit = detect_audit([empty, short, shared_a, shared_b, same_account])
        self.assertEqual(audit['weak'], [short.id])
        self.assertEqual(audit['reused'], [[shared_a.id, shared_b.id, same_account.id]])
        self.assertIn(empty.id, audit['incomplete'])

    def test_audit_reuse_uses_the_same_origin_rule_as_the_cli(self):
        local_a = candidate('http://127.0.0.1:8080/', 'admin', 'fake-local-123456')
        local_b = candidate('http://127.0.0.1:9090/', 'admin', 'fake-local-123456')
        login = candidate('https://github.com/login', 'alice', 'fake-same-123456')
        session = candidate('https://github.com/session', 'alice', 'fake-same-123456')
        self.assertEqual(detect_audit([local_a, local_b, login, session])['reused'], [[local_a.id, local_b.id]])


if __name__ == '__main__':
    unittest.main()
