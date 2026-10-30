"""What the review screen shows: records, duplicate groups, audit and stats. Passwords stay out."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..domain.accounts import duplicate_key
from ..domain.reuse import reused_password_groups
from ..domain.strength import is_weak
from ..domain.urls import parse_url
from .candidate import Candidate, identity


def kind_of(url: str) -> str:
    return 'android' if url.lower().startswith(('androidapp://', 'android://')) else 'web'


def canonical_url(row: Candidate) -> Any:
    # Compare normalized URLs, preserving paths, ports and protocols.
    url = parse_url(identity(row).url)
    return None if url.invalid or url.embedded_auth else url.key


def summarize(row: Candidate) -> dict[str, Any]:
    url = parse_url(row.url)
    return {
        'id': row.id, 'name': row.name, 'url': row.url,
        'username': row.username, 'type': kind_of(row.url),
        'source': row.original.source, 'line': row.original.line,
        'included': row.included, 'review': row.review,
        'http': url.insecure_http, 'invalid_uri': url.invalid, 'embedded_auth': url.embedded_auth,
        'host': url.host,
    }


def detail(row: Candidate) -> dict[str, Any]:
    """One record with its secrets, for the editor only."""
    return {**summarize(row), 'password': row.password, 'note': row.note,
            'original': {'name': row.original.name, 'url': row.original.url,
                         'username': row.original.username, 'source': row.original.source,
                         'line': row.original.line}}


def detect_groups(rows: list[Candidate]) -> list[dict[str, Any]]:
    by_uri: dict[Any, list[Candidate]] = defaultdict(list)
    for row in rows:
        if not row.included:
            continue
        key = canonical_url(row)
        if key is not None:
            by_uri[key].append(row)
    result = []
    for _, members in by_uri.items():
        if len(members) < 2:
            continue
        base = members[0]
        by_user: dict[str, set[str]] = defaultdict(set)
        for r in members:
            by_user[r.username].add(r.password)
        conflict = any(len(passwords) > 1 for passwords in by_user.values())
        # Exact only when merge_exact would merge the whole group.
        keys = {duplicate_key(identity(r)) for r in members}
        exact = len(keys) == 1 and None not in keys
        category = 'conflict' if conflict else ('exact' if exact else 'multiple-accounts')
        result.append({
            'id': base.id, 'kind': category, 'name': base.name,
            'url': base.url, 'username': base.username, 'type': kind_of(base.url),
            'members': [{**summarize(r),
                         'match_url': canonical_url(r) == canonical_url(base),
                         'match_username': r.username == base.username,
                         'match_password': r.password == base.password} for r in members],
            'count': len(members),
            'pending': any(r.review == 'pending' for r in members),
        })
    weight = {'conflict': 0, 'exact': 1, 'multiple-accounts': 2}
    return sorted(result, key=lambda g: (weight[g['kind']], g['name'].casefold(), g['username'].casefold()))


def detect_audit(rows: list[Candidate]) -> dict[str, Any]:
    active = [r for r in rows if r.included]
    weak = [r.id for r in active if is_weak(r.password)]
    incomplete = [r.id for r in active
                  if not r.url or not r.username or not r.password or parse_url(r.url).invalid]
    reused = [[r.id for r in group] for group in reused_password_groups(active)]
    return {'reused': reused, 'weak': weak, 'incomplete': incomplete, 'breaches': 'not_checked'}


def review_state(records: list[Candidate], files: list[dict[str, Any]],
                 can_undo: bool, session_saved: bool) -> dict[str, Any]:
    active = [r for r in records if r.included]
    return {
        'files': list(files),
        'records': [summarize(r) for r in records],
        'groups': detect_groups(records),
        'audit': detect_audit(records),
        'stats': {
            'total': len(records), 'included': len(active),
            'excluded': len(records) - len(active),
            'reviewed': sum(r.review != 'pending' for r in records),
            'verified': sum(r.review == 'verified' for r in records),
        },
        'can_undo': can_undo,
        'session_saved': session_saved,
    }
