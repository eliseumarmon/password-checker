"""Domain rules through their public functions; fictional credentials only."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.domain.accounts import account_key, duplicate_key, masked_username, origin_account  # noqa: E402
from backend.password_checker.domain.consolidation import consolidate  # noqa: E402
from backend.password_checker.domain.credential import Credential  # noqa: E402
from backend.password_checker.domain.notes import NOTE_SEPARATOR, combine_notes  # noqa: E402
from backend.password_checker.domain.reuse import shared_password_groups  # noqa: E402
from backend.password_checker.domain.strength import Strength, assess_strength, is_weak  # noqa: E402
from backend.password_checker.domain.urls import (  # noqa: E402
    bitwarden_uri, is_android_source, parse_url, supported_uri, web_origin,
)


def cred(url, username, password, note='', name='Site', source='chrome'):
    return Credential(source, 2, name, url, username, password, note)


class UrlTests(unittest.TestCase):
    def test_web_url_keeps_path_and_flags_insecure_http(self):
        secure = parse_url('https://Example.org')
        self.assertEqual(secure.host, 'example.org')
        self.assertEqual(secure.key, ('https', 'example.org', '/', '', ''))
        self.assertFalse(secure.insecure_http)
        self.assertTrue(parse_url('http://example.org/login').insecure_http)
        self.assertNotEqual(parse_url('https://example.org/a').key, parse_url('https://example.org/b').key)

    def test_invalid_and_embedded_credentials(self):
        self.assertTrue(parse_url('ftp://example.org').invalid)
        self.assertTrue(parse_url('').invalid)
        self.assertTrue(parse_url('https://user:pw@example.org').embedded_auth)

    def test_android_source_identity_includes_signature(self):
        first = parse_url('android://SIGN-A@com.example.app/')
        second = parse_url('android://SIGN-B@com.example.app/')
        self.assertEqual(first.host, 'com.example.app')
        self.assertNotEqual(first.key, second.key)
        self.assertTrue(is_android_source(' android://SIGN-A@com.example.app/ '))
        self.assertFalse(is_android_source('androidapp://com.example.app'))
        self.assertEqual(bitwarden_uri('android://SIGN@Com.Example.App/'), 'androidapp://com.example.app')
        self.assertEqual(bitwarden_uri('https://example.org'), 'https://example.org')

    def test_supported_uri_requires_explicit_known_scheme(self):
        self.assertTrue(supported_uri('https://example.org'))
        self.assertFalse(supported_uri('example.org'))
        self.assertFalse(supported_uri(' https://example.org'))

    def test_web_origin_never_leaks_path_query_or_userinfo(self):
        self.assertEqual(web_origin('https://Host.invalid:8443/reset/TOKEN?key=x#f'), 'https://host.invalid:8443/')
        self.assertEqual(web_origin('http://host.invalid:80/a'), 'http://host.invalid/')
        self.assertIsNone(web_origin('https://user:pw@host.invalid/'))
        self.assertIsNone(web_origin('androidapp://com.example.app'))
        self.assertIsNone(web_origin('https://host.invalid:99999/'))


class StrengthTests(unittest.TestCase):
    def test_levels_in_priority_order(self):
        self.assertIs(assess_strength(''), Strength.EMPTY)
        self.assertIs(assess_strength('Password123'), Strength.OBVIOUS)
        self.assertIs(assess_strength('aaaaaaaaaaaaaaaa'), Strength.OBVIOUS)
        self.assertIs(assess_strength('fake-1234'), Strength.SHORT)
        self.assertIs(assess_strength('fake-12345678'), Strength.MODERATE)
        self.assertIs(assess_strength('fake-1234567890'), Strength.ACCEPTABLE)

    def test_weak_means_obvious_or_short_but_not_empty(self):
        self.assertTrue(is_weak('qwerty'))
        self.assertTrue(is_weak('fake-1234'))
        self.assertFalse(is_weak(''))
        self.assertFalse(is_weak('fake-12345678'))


class AccountTests(unittest.TestCase):
    def test_ambiguous_accounts_have_no_identity(self):
        self.assertIsNone(account_key(cred('https://example.org', '', 'fake-123')))
        self.assertIsNone(account_key(cred('ftp://example.org', 'alice', 'fake-123')))
        self.assertIsNone(duplicate_key(cred('https://example.org', 'alice', '')))
        self.assertEqual(duplicate_key(cred('https://example.org/', 'alice', 'fake-123')),
                         duplicate_key(cred('https://EXAMPLE.org', 'alice', 'fake-123')))

    def test_usernames_are_case_sensitive(self):
        self.assertNotEqual(account_key(cred('https://example.org', 'Alice', 'x')),
                            account_key(cred('https://example.org', 'alice', 'x')))

    def test_origin_account_is_scheme_host_port_and_username(self):
        same = origin_account(cred('https://Example.org/login?x=1', 'alice', 'x'))
        self.assertEqual(same, origin_account(cred('https://example.org:443/settings', 'alice', 'x')))
        self.assertNotEqual(origin_account(cred('http://127.0.0.1:8080/', 'admin', 'x')),
                            origin_account(cred('http://127.0.0.1:9090/', 'admin', 'x')))
        self.assertNotEqual(same, origin_account(cred('http://example.org/login', 'alice', 'x')))
        self.assertEqual(origin_account(cred('android://SIGN@com.example.app/', 'eve', 'x')),
                         origin_account(cred('androidapp://com.example.app', 'eve', 'x')))
        self.assertIsNone(origin_account(cred('ftp://example.org', 'alice', 'x')))
        self.assertIsNone(origin_account(cred('https://example.org', '', 'x')))

    def test_masked_username(self):
        self.assertEqual(masked_username('alice@example.org'), 'al***@example.org')
        self.assertEqual(masked_username('@example.org'), '***@example.org')
        self.assertEqual(masked_username('alice'), 'al***')
        self.assertEqual(masked_username('ab'), '**')
        self.assertEqual(masked_username(''), '(sin usuario)')


class NotesTests(unittest.TestCase):
    def test_combines_distinct_non_blank_notes_in_order(self):
        self.assertEqual(combine_notes(['a', ' ', 'b', 'a']), 'a' + NOTE_SEPARATOR + 'b')
        self.assertEqual(combine_notes(['solo']), 'solo')
        self.assertEqual(combine_notes(['', '  ']), '')


class ReuseTests(unittest.TestCase):
    def test_groups_only_passwords_shared_by_distinct_accounts(self):
        shared_a = cred('https://a.invalid', 'alice', 'fake-shared-1')
        shared_b = cred('https://b.invalid', 'alice', 'fake-shared-1')
        same_account = cred('https://c.invalid', 'carol', 'fake-own-2')
        same_account_copy = cred('https://c.invalid', 'carol', 'fake-own-2')
        no_account = cred('https://d.invalid', '', 'fake-shared-1')
        empty = cred('https://e.invalid', 'erin', '')
        groups = shared_password_groups(
            [shared_a, shared_b, same_account, same_account_copy, no_account, empty],
            lambda c: (parse_url(c.url).host, c.username) if c.username else None)
        self.assertEqual(groups, [[shared_a, shared_b]])


class ConsolidationTests(unittest.TestCase):
    def test_merges_exact_duplicates_and_keeps_conflicts(self):
        rows = [cred('https://example.org/login', 'alice', 'fake-current-123', 'first'),
                cred('https://example.org/login', 'alice', 'fake-current-123', 'second', source='brave'),
                cred('https://example.org/login', 'alice', 'fake-old-1234567')]
        merged, stats = consolidate(rows)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].note, 'first' + NOTE_SEPARATOR + 'second')
        self.assertEqual(stats['duplicates'], 1)
        self.assertEqual(len(stats['conflicts']), 1)
        self.assertEqual({r.password for r in stats['conflicts'][0]}, {'fake-current-123', 'fake-old-1234567'})

    def test_reuse_separates_local_ports_but_not_paths_of_one_site(self):
        _, stats = consolidate([cred('http://127.0.0.1:8080/', 'admin', 'fake-local-123456'),
                                cred('http://127.0.0.1:9090/', 'admin', 'fake-local-123456')])
        self.assertEqual((stats['reused_groups'], stats['reused_accounts']), (1, 2))
        _, stats = consolidate([cred('https://github.com/login', 'alice', 'fake-same-123456'),
                                cred('https://github.com/session', 'alice', 'fake-same-123456')])
        self.assertEqual((stats['reused_groups'], stats['reused_accounts']), (0, 0))

    def test_reuse_and_related_metrics(self):
        rows = [cred('https://a.invalid/login', 'alice', 'fake-shared-123456'),
                cred('https://a.invalid/other', 'alice', 'fake-shared-123456'),
                cred('https://b.invalid', 'bob', 'fake-shared-123456'),
                cred('https://c.invalid', 'carol', 'fake-unique-123456')]
        _, stats = consolidate(rows)
        # Same domain + user on two paths is one reuse account, but a possible relation.
        self.assertEqual(stats['reused_groups'], 1)
        self.assertEqual(stats['reused_accounts'], 2)
        self.assertEqual(len(stats['possible_related']), 1)
        self.assertEqual(len(stats['possible_related'][0]), 2)

    def test_android_source_uri_converted_and_preserved_in_notes(self):
        merged, stats = consolidate([cred('android://SIGN@com.example.app/', 'eve', 'fake-app-123456', name='')])
        self.assertEqual(merged[0].url, 'androidapp://com.example.app')
        self.assertEqual(merged[0].name, 'com.example.app')
        self.assertIn('URI Android de origen: android://SIGN@com.example.app/', merged[0].note)
        self.assertEqual(stats['android_apps'], 1)


if __name__ == '__main__':
    unittest.main()
