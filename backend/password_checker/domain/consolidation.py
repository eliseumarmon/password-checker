"""Consolidation of browser exports for Bitwarden; never touches the disk.

Exact duplicates (same URL, exact username and password) are merged.
Conflicts and possibly related accounts are only reported: different
passwords are always kept so the user can decide which one is valid.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Sequence, Tuple

from .accounts import account_key, duplicate_key, host_account, origin_account
from .credential import Credential
from .notes import combine_notes
from .reuse import reused_password_groups
from .strength import MIN_LENGTH, RECOMMENDED_LENGTH, is_obviously_weak
from .urls import android_package, bitwarden_uri, is_android_source, parse_url

Group = List[Credential]


def group_exact_duplicates(rows: Sequence[Credential]) -> List[Group]:
    """Rows without a safe duplicate key always stay in a group of their own."""
    groups: Dict[Any, Group] = {}
    unique: List[Group] = []
    for row in rows:
        key = duplicate_key(row)
        if key is None:
            unique.append([row])
        elif key in groups:
            groups[key].append(row)
        else:
            group = [row]
            groups[key] = group
            unique.append(group)
    return unique


def merge_group(records: Group) -> Credential:
    """Preserva notas distintas sin exponerlas en los informes."""
    first = records[0]
    chosen = next((r.name for r in records if r.name.strip()), "")
    if not chosen:
        chosen = android_package(first.url) or parse_url(first.url).host or "Acceso sin nombre"
    return Credential(first.source, first.line, chosen, bitwarden_uri(first.url),
                      first.username, first.password, combine_notes(r.note for r in records))


def find_conflicts(unique: Sequence[Group], merged: Sequence[Credential]) -> List[Group]:
    """Same account (original URI + username) with different passwords."""
    accounts: Dict[Any, Group] = defaultdict(list)
    for group, row in zip(unique, merged):
        key = account_key(group[0])  # Use original URI for identity.
        if key is not None:
            accounts[key].append(row)
    return [group for group in accounts.values() if len({r.password for r in group}) > 1]


def find_possible_related(unique: Sequence[Group], merged: Sequence[Credential]) -> List[Group]:
    """Same domain and username on different URLs: warn only, never merge."""
    by_host_user: Dict[Tuple[str, str], List[Tuple[Credential, Credential]]] = defaultdict(list)
    for group, row in zip(unique, merged):
        original = group[0]  # Merged rows keep the original username.
        key = host_account(original)
        if key is not None:
            by_host_user[key].append((original, row))
    return [[row for _, row in g] for g in by_host_user.values()
            if len({account_key(original) for original, _ in g}) > 1]


def consolidate(rows: Sequence[Credential]) -> Tuple[List[Credential], Dict[str, Any]]:
    """Return the consolidated credentials and review metrics."""
    unique = group_exact_duplicates(rows)
    output_rows = [merge_group(group) for group in unique]
    reused = reused_password_groups(output_rows)
    reused_accounts = {origin_account(r) for group in reused for r in group}
    # Length and pattern metrics are independent, overlapping counters (a short
    # common password counts in both), unlike the exclusive assess_strength().
    distinct_passwords = set(r.password for r in output_rows if r.password)
    urls = [parse_url(r.url) for r in output_rows]
    stats = {
        "originals": len(rows),
        "by_source": Counter(row.source for row in rows),
        "final": len(output_rows),
        "duplicates": len(rows) - len(output_rows),
        "notes_merged": sum(len(set(r.note for r in g if r.note.strip())) > 1 for g in unique),
        "conflicts": find_conflicts(unique, output_rows),
        "possible_related": find_possible_related(unique, output_rows),
        "reused_groups": len(reused),
        "reused_accounts": len(reused_accounts),
        "short": sum(len(password) < MIN_LENGTH for password in distinct_passwords),
        "moderate": sum(MIN_LENGTH <= len(password) < RECOMMENDED_LENGTH for password in distinct_passwords),
        "obvious": sum(is_obviously_weak(password) for password in distinct_passwords),
        "empty_password": sum(not r.password for r in output_rows),
        "empty_username": sum(not r.username for r in output_rows),
        "empty_url": sum(not r.url for r in output_rows),
        "http": sum(url.insecure_http for url in urls),
        "invalid_url": sum(url.invalid for r, url in zip(output_rows, urls) if r.url),
        "android_apps": sum(is_android_source(g[0].url) for g in unique),
        "url_credentials": sum(url.embedded_auth for url in urls),
        "undedupeable": sum(duplicate_key(r) is None for r in rows),
        "merged_per_row": {id(row): len(group) - 1 for group, row in zip(unique, output_rows)},
    }
    return output_rows, stats
