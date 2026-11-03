"""HTTP contract tests with synthetic data; no production secrets."""
import csv
import io
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


def without_warnings(import_response):
    """The import response is the workspace snapshot plus the warnings channel."""
    return {key: value for key, value in import_response.items() if key != 'warnings'}


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
        self.assertEqual(before['warnings'], [])
        self.assertEqual(self.client.get('/api/workspace').json(), without_warnings(before))

    def test_rejected_merge_and_trash_are_client_errors_that_change_nothing(self):
        before = self.import_exact_copies()
        with patch.object(limits, 'MAX_SNAPSHOT_TEXT_CHARS', 30):
            merged = self.client.post('/api/merge-exact')
        self.assertEqual(merged.status_code, 422)
        self.assertIn('«notas»', merged.json()['detail'])
        # Measured in plaintext bytes: the real .pwc size rounds to Base64 blocks of 3 bytes,
        # so the one byte that trashing adds ("false") would only sometimes make the file grow.
        with patch.object(limits, 'MAX_SESSION_BYTES', 64), \
                patch.object(limits, 'session_file_size', lambda plaintext_bytes: plaintext_bytes):
            trashed = self.client.post('/api/records/trash', json={'ids': [before['records'][0]['id']]})
        self.assertEqual(trashed.status_code, 422)
        self.assertNotIn('fictional-secret-123', merged.text + trashed.text)
        self.assertEqual(before['warnings'], [])
        self.assertEqual(self.client.get('/api/workspace').json(), without_warnings(before))

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

    def test_import_over_a_session_limit_is_a_422_that_changes_nothing(self):
        before = self.import_exact_copies()
        rows = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-secret-321,\n'
        rows += b'B,https://b.invalid/,bob,fictional-secret-654,\n'
        with patch.object(limits, 'MAX_SESSION_RECORDS', 1):
            response = self.client.post('/api/import', files=[('files', ('chrome.csv', rows, 'text/csv'))])
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn('como máximo 1 credenciales', response.json()['detail'])
        self.assertNotIn('fictional-secret', response.text)
        self.assertEqual(self.client.get('/api/workspace').json(), without_warnings(before))

    def test_edit_over_a_session_limit_is_a_422_that_changes_nothing(self):
        before = self.import_exact_copies()
        secret = 'fictional-secret-note-' + 'x' * 30
        with patch.object(limits, 'MAX_SNAPSHOT_TEXT_CHARS', 30):
            response = self.client.patch(f"/api/records/{before['records'][0]['id']}", json={'note': secret})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn('«notas»', response.json()['detail'])
        self.assertNotIn(secret, response.text)
        self.assertEqual(self.client.get('/api/workspace').json(), without_warnings(before))

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

    def test_safari_totp_survives_a_v2_session_and_a_v1_session_is_refused(self):
        from backend.password_checker.infrastructure.sessions import encrypt_session
        payload = (b'Title,URL,Username,Password,Notes,OTPAuth\n'
                   b'A,https://example.invalid/,alice,fictional-123456,,otpauth://totp/fictional-imported\n')
        imported = self.client.post('/api/import', files=[('files', ('Passwords.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        identifier = imported.json()['records'][0]['id']
        workspace.change(identifier, {'totp': 'otpauth://totp/fictional-edited'})
        passphrase = 'fictional-session-passphrase-12345'
        saved = self.client.post('/api/session/save', json={'passphrase': passphrase})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertNotIn(b'fictional-edited', saved.content)
        workspace.change(identifier, {'totp': ''})

        restored = self.client.post('/api/session/load', data={'passphrase': passphrase},
                                    files={'file': ('session.pwc', saved.content, 'application/octet-stream')})
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertNotIn('fictional-', restored.text.replace('fictional-123456', ''))
        row = workspace._records[identifier]
        self.assertEqual((row.original.totp, row.totp),
                         ('otpauth://totp/fictional-imported', 'otpauth://totp/fictional-edited'))

        legacy = workspace.serialize()
        legacy['version'] = 1
        for record in legacy['records']:
            del record['totp'], record['original']['totp']
        before = workspace.snapshot()
        refused = self.client.post('/api/session/load', data={'passphrase': passphrase},
                                   files={'file': ('old.pwc', encrypt_session(legacy, passphrase),
                                                   'application/octet-stream')})
        self.assertEqual(refused.status_code, 422)
        self.assertIn('versión anterior', refused.json()['detail'])
        self.assertEqual(workspace.snapshot(), before)

    def test_export_writes_the_current_totp_of_each_record(self):
        payload = (b'Title,URL,Username,Password,Notes,OTPAuth\n'
                   b'A,https://a.invalid/,alice,fictional-1,,otpauth://totp/fictional-a\n'
                   b'B,https://b.invalid/,bob,fictional-2,,otpauth://totp/fictional-b\n'
                   b'C,https://c.invalid/,carol,fictional-3,,\n')
        imported = self.client.post('/api/import', files=[('files', ('Passwords.csv', payload, 'text/csv'))]).json()
        ids = {record['username']: record['id'] for record in imported['records']}
        workspace.change(ids['bob'], {'totp': 'otpauth://totp/fictional-b-edited'})
        exported = self.client.get('/api/export')
        self.assertEqual(exported.status_code, 200, exported.text)
        rows = csv.DictReader(io.StringIO(exported.content.decode('utf-8-sig')))
        self.assertEqual({row['login_username']: row['login_totp'] for row in rows},
                         {'alice': 'otpauth://totp/fictional-a', 'bob': 'otpauth://totp/fictional-b-edited', 'carol': ''})

    def test_two_different_totps_survive_merging_and_reach_the_export(self):
        payload = (b'Title,URL,Username,Password,Notes,OTPAuth\n'
                   b'A,https://a.invalid/,alice,fictional-1,,otpauth://totp/fictional-a1\n'
                   b'A,https://a.invalid/,alice,fictional-1,,otpauth://totp/fictional-a2\n'
                   b'A,https://a.invalid/,alice,fictional-1,,\n'
                   b'B,https://b.invalid/,bob,fictional-2,,\n'
                   b'B,https://b.invalid/,bob,fictional-2,,otpauth://totp/fictional-b\n')
        imported = self.client.post('/api/import', files=[('files', ('Passwords.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        merged = self.client.post('/api/merge-exact')
        self.assertEqual(merged.status_code, 200, merged.text)
        # Only bob's copies merge: alice's group holds two different TOTPs.
        self.assertEqual(merged.json()['stats']['excluded'], 1)
        rows = list(csv.DictReader(io.StringIO(self.client.get('/api/export').content.decode('utf-8-sig'))))
        self.assertEqual(sorted((row['login_username'], row['login_totp']) for row in rows), [
            ('alice', ''), ('alice', 'otpauth://totp/fictional-a1'), ('alice', 'otpauth://totp/fictional-a2'),
            ('bob', 'otpauth://totp/fictional-b')])

    def test_totp_travels_only_in_the_record_detail(self):
        secret = 'otpauth://totp/FICTIONAL-T6-SECRET'
        payload = (b'Title,URL,Username,Password,Notes,OTPAuth\n'
                   b'A,https://a.invalid/,alice,fictional-1,,' + secret.encode() + b'\n'
                   b'A,https://a.invalid/,alice,fictional-1,,\n'
                   b'B,https://b.invalid/,bob,fictional-1,,\n')
        imported = self.client.post('/api/import', files=[('files', ('Passwords.csv', payload, 'text/csv'))])
        state = imported.json()
        self.assertEqual(state['groups'][0]['kind'], 'exact')
        self.assertTrue(state['audit']['reused'])
        ids = [record['id'] for record in state['records']]
        responses = [imported, self.client.get('/api/workspace'),
                     self.client.post('/api/merge-exact'), self.client.post('/api/undo'),
                     self.client.post('/api/records/trash', json={'ids': ids[:1]}),
                     self.client.patch('/api/records/' + ids[0], json={'included': True}),
                     self.client.patch('/api/records/' + ids[1], json={'totp': secret + '-EDITED'})]
        for response in responses:
            with self.subTest(url=str(response.request.url)):
                self.assertEqual(response.status_code, 200, response.text)
                self.assertNotIn('FICTIONAL-T6-SECRET', response.text)
                self.assertNotIn('totp', response.text)
        details = {i: self.client.get('/api/records/' + i).json() for i in ids}
        self.assertEqual([details[i]['totp'] for i in ids], [secret, secret + '-EDITED', ''])
        # The editor gets the current secret only; the immutable original stays out, like the password.
        self.assertNotIn('totp', details[ids[0]]['original'])

    def test_validation_errors_never_echo_the_submitted_values(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid,u,fake-1,\n'
        identifier = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))]).json()['records'][0]['id']
        before = self.client.get('/api/records/' + identifier).json()
        for body in ({'totp': 'otpauth://totp/FICTIONAL-T6-' + 'x' * 5000},
                     {'password': 'FICTIONAL-T6-' + 'x' * 9000},
                     {'totp': ['FICTIONAL-T6-list']},
                     {'note': 'FICTIONAL-T6-note', 'unknown': 'FICTIONAL-T6-extra'}):
            with self.subTest(fields=sorted(body)):
                response = self.client.patch('/api/records/' + identifier, json=body)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('FICTIONAL-T6', response.text)
                self.assertTrue(all(set(error) == {'type', 'loc', 'msg'} for error in response.json()['detail']))
        self.assertEqual(self.client.get('/api/records/' + identifier).json(), before)
        # The same rule holds on every endpoint, not only the record edit.
        for path, body in (('/api/records/trash', {'ids': 'FICTIONAL-T6-ids'}),
                           ('/api/session/save', {'passphrase': ['FICTIONAL-T6-passphrase']})):
            with self.subTest(path=path):
                response = self.client.post(path, json=body)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('FICTIONAL-T6', response.text)
                self.assertEqual(response.json()['detail'][0]['loc'][0], 'body')

    def test_the_totp_can_be_set_up_to_its_limit_and_cleared_through_the_api(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid,u,fake-1,\n'
        identifier = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))]).json()['records'][0]['id']
        longest = 'otpauth://totp/' + 'x' * (4096 - 15)
        for value, status in ((longest, 200), ('', 200), (None, 422)):
            with self.subTest(length=None if value is None else len(value)):
                response = self.client.patch('/api/records/' + identifier, json={'totp': value})
                self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(self.client.get('/api/records/' + identifier).json()['totp'], '')
        self.client.patch('/api/records/' + identifier, json={'totp': longest})
        self.assertEqual(self.client.get('/api/records/' + identifier).json()['totp'], longest)

    def test_a_blank_otpauth_cell_never_blocks_a_merge_and_real_totps_reach_the_export_verbatim(self):
        padded = '  otpauth://totp/fictional-padded \t'
        payload = ('Title,URL,Username,Password,Notes,OTPAuth\n'
                   'A,https://a.invalid/,alice,fictional-1,,otpauth://totp/fictional-a\n'
                   'A,https://a.invalid/,alice,fictional-1,,"   "\n'
                   'B,https://b.invalid/,bob,fictional-2,,"\t"\n'
                   'B,https://b.invalid/,bob,fictional-2,,\n'
                   f'C,https://c.invalid/,carol,fictional-3,,"{padded}"\n').encode()
        imported = self.client.post('/api/import', files=[('files', ('Passwords.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        self.assertEqual(sorted(group['kind'] for group in imported.json()['groups']), ['exact', 'exact'])
        merged = self.client.post('/api/merge-exact')
        self.assertEqual(merged.json()['stats']['excluded'], 2)
        rows = csv.DictReader(io.StringIO(self.client.get('/api/export').content.decode('utf-8-sig')))
        self.assertEqual(sorted((row['login_username'], row['login_totp']) for row in rows), [
            ('alice', 'otpauth://totp/fictional-a'), ('bob', ''), ('carol', padded)])

    def test_unknown_origin_survives_encrypted_session_round_trip(self):
        payload = b'url,username,password\nhttps://example.invalid/,alice,fictional-secret-123\n'
        imported = self.client.post('/api/import', files=[('files', ('export.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        before = imported.json()
        self.assertEqual(before['files'][0]['source'], 'unknown')
        self.assertEqual(before['records'][0]['source'], 'unknown')
        passphrase = 'fictional-session-passphrase-12345'
        saved = self.client.post('/api/session/save', json={'passphrase': passphrase})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertNotIn(b'fictional-secret-123', saved.content)
        other = b'url,username,password\nhttps://other.invalid/,bob,fictional-other-123\n'
        self.client.post('/api/import', files=[('files', ('other.csv', other, 'text/csv'))])
        restored = self.client.post('/api/session/load', data={'passphrase': passphrase},
                                    files={'file': ('session.pwc', saved.content, 'application/octet-stream')})
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertEqual(restored.json()['files'], before['files'])
        self.assertEqual(restored.json()['records'], before['records'])
        detail = self.client.get('/api/records/' + before['records'][0]['id']).json()
        self.assertEqual((detail['original']['source'], detail['password']), ('unknown', 'fictional-secret-123'))

    def test_session_passphrase_length_boundary(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        self.assertEqual(self.client.post('/api/session/save', json={'passphrase': 'x' * 11}).status_code, 422)
        accepted = self.client.post('/api/session/save', json={'passphrase': 'x' * 12})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(self.client.post('/api/session/save', json={'passphrase': 'x' * 1025}).status_code, 422)

    def test_import_response_always_carries_warnings_and_never_discarded_values(self):
        payload = (b'name,url,username,password,note,extra_secret\n'
                   b'A,https://a.invalid/,alice,fictional-123456,,fictional-discarded-xyz\n')
        response = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))])
        self.assertEqual(response.status_code, 200, response.text)
        state = response.json()
        self.assertEqual(state['warnings'], [{'file': 'chrome.csv', 'imported_count': 1,
                                              'columns': [{'column': 'extra_secret', 'rows': 1}]}])
        self.assertEqual(state['stats']['total'], 1)
        self.assertNotIn('fictional-discarded-xyz', response.text)

    def test_import_without_warnings_returns_an_empty_list(self):
        payload = b'name,url,username,password,note\nA,https://a.invalid/,alice,fictional-123456,\n'
        response = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['warnings'], [])

    def test_import_warnings_are_per_file_with_base_name_and_imported_count(self):
        warnable = (b'url,username,password,guid\n'
                    b'https://a.invalid/,alice,fictional-111,fictional-guid-1\n'
                    b'https://b.invalid/,bob,fictional-222,\n')
        clean = b'name,url,username,password,note\nC,https://c.invalid/,carol,fictional-333,\n'
        response = self.client.post('/api/import', files=[
            ('files', ('dir/sub\\warn.csv', warnable, 'text/csv')),
            ('files', ('clean.csv', clean, 'text/csv')),
        ])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['warnings'], [
            {'file': 'warn.csv', 'imported_count': 2, 'columns': [{'column': 'guid', 'rows': 1}]}])
        self.assertNotIn('fictional-guid-1', response.text)

    def test_warnings_stay_out_of_workspace_session_and_export(self):
        payload = (b'name,url,username,password,note,extra_secret\n'
                   b'A,https://a.invalid/,alice,fictional-123456,,fictional-discarded-xyz\n')
        imported = self.client.post('/api/import', files=[('files', ('chrome.csv', payload, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        self.assertEqual(len(imported.json()['warnings']), 1)
        workspace_json = self.client.get('/api/workspace').json()
        self.assertNotIn('warnings', workspace_json)
        self.assertNotIn('fictional-discarded-xyz', str(workspace_json))
        passphrase = 'fictional-session-passphrase-12345'
        saved = self.client.post('/api/session/save', json={'passphrase': passphrase})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertNotIn(b'fictional-discarded-xyz', saved.content)
        restored = self.client.post('/api/session/load', data={'passphrase': passphrase},
                                    files={'file': ('session.pwc', saved.content, 'application/octet-stream')})
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertNotIn('warnings', restored.json())
        self.assertNotIn('fictional-discarded-xyz', restored.text)
        export = self.client.get('/api/export')
        self.assertEqual(export.status_code, 200)
        self.assertNotIn(b'fictional-discarded-xyz', export.content)

    def test_failed_import_keeps_workspace_snapshot_and_history(self):
        warnable = b'url,username,password,extra\nhttps://a.invalid/,alice,fictional-111,fictional-x\n'
        imported = self.client.post('/api/import', files=[('files', ('a.csv', warnable, 'text/csv'))])
        self.assertEqual(imported.status_code, 200, imported.text)
        self.assertEqual(len(imported.json()['warnings']), 1)
        identifier = imported.json()['records'][0]['id']
        self.client.patch('/api/records/' + identifier, json={'review': 'verified'})
        before = workspace.snapshot()
        self.assertTrue(before['can_undo'])
        self.assertNotIn('warnings', before)
        good = b'name,url,username,password,note\nC,https://c.invalid/,carol,fictional-333,\n'
        bad = b'name,url,username,password,note\nB,https://b.invalid/,bob,"fictional-bad"x,\n'
        response = self.client.post('/api/import', files=[('files', ('ok.csv', good, 'text/csv')),
                                                          ('files', ('bad.csv', bad, 'text/csv'))])
        self.assertEqual(response.status_code, 422, response.text)
        self.assertNotIn('fictional-bad', response.text)
        self.assertEqual(workspace.snapshot(), before)

    def test_cross_origin_rejected_and_no_cache(self):
        response = self.client.get('/api/workspace', headers={'Origin': 'https://evil.example'})
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/api/workspace')
        self.assertEqual(response.headers['cache-control'], 'no-store')


if __name__ == '__main__':
    unittest.main()
