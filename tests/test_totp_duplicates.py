"""S6: exact copies and TOTP secrets. Fictional credentials and TOTP URIs only."""
import sys
import unittest
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.password_checker.application.candidate import Candidate
from backend.password_checker.application.workspace import Workspace
from backend.password_checker.domain.credential import Credential

T1 = 'otpauth://totp/fictional-one'
T2 = 'otpauth://totp/fictional-two'


def workspace_with(totps):
    """One identity group (same URL, user and password) whose copies differ only in their TOTP."""
    workspace = Workspace()
    rows = [Candidate.from_source(Credential('safari', line, 'Site', 'https://site.invalid/', 'alice',
                                             'fictional-pw-123', '', totp))
            for line, totp in enumerate(totps, start=2)]
    workspace._records = {row.id: row for row in rows}
    return workspace


def kept_totps(workspace):
    return sorted(row.totp for row in workspace._records.values() if row.included)


def group_kinds(workspace):
    return [group['kind'] for group in workspace.snapshot()['groups']]


class TotpDuplicateTests(unittest.TestCase):
    def test_the_four_pairs_of_s6(self):
        cases = {
            (T1, T1): [T1],          # same TOTP: an exact copy
            ('', ''): [''],          # no TOTP: today's rule
            ('', T1): [T1],          # only one TOTP: merged, and it is kept
            (T1, ''): [T1],
            (T1, T2): [T1, T2],      # two different TOTPs: never merged
        }
        for totps, expected in cases.items():
            with self.subTest(totps=totps):
                workspace = workspace_with(totps)
                self.assertEqual(group_kinds(workspace), ['exact' if len(expected) == 1 else 'multiple-accounts'])
                workspace.merge_exact()
                self.assertEqual(kept_totps(workspace), expected)

    def test_a_copy_without_totp_never_bridges_two_different_totps(self):
        for order in permutations(['', T1, T2]):
            with self.subTest(order=order):
                workspace = workspace_with(order)
                self.assertEqual(group_kinds(workspace), ['multiple-accounts'])
                workspace.merge_exact()
                self.assertEqual(kept_totps(workspace), ['', T1, T2])
                self.assertFalse(workspace.snapshot()['can_undo'])

    def test_copies_without_totp_merge_into_the_single_totp(self):
        for order in set(permutations(['', '', T1])):
            with self.subTest(order=order):
                workspace = workspace_with(order)
                self.assertEqual(group_kinds(workspace), ['exact'])
                workspace.merge_exact()
                self.assertEqual(kept_totps(workspace), [T1])
                workspace.undo()
                self.assertEqual([row.totp for row in workspace._records.values()], list(order))

    def test_no_copy_merges_when_the_group_holds_two_different_totps(self):
        for order in set(permutations(['', '', T1, T2])):
            with self.subTest(order=order):
                workspace = workspace_with(order)
                workspace.merge_exact()
                self.assertEqual(kept_totps(workspace), ['', '', T1, T2])

    def test_a_later_merge_keeps_a_totp_already_kept(self):
        workspace = workspace_with(['', T1])
        workspace.merge_exact()
        self.assertEqual(kept_totps(workspace), [T1])
        later = Candidate.from_source(Credential('safari', 9, 'Site', 'https://site.invalid/', 'alice',
                                                 'fictional-pw-123', ''))
        workspace._records = {later.id: later, **workspace._records}
        workspace.merge_exact()
        self.assertEqual(kept_totps(workspace), [T1])


if __name__ == '__main__':
    unittest.main()
