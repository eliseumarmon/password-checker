"""In-memory review workspace. No HTTP or UI dependencies.

The existing CSV reader stays the single source of truth during migration.
Original credentials are immutable; candidate edits never change imports.
"""
from __future__ import annotations

import csv
import io
import secrets
import threading
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from auditar_contrasenas_local import (
    BITWARDEN_FIELDS, Credential, account_key, bitwarden_uri,
    read_export, simple_weak, url_parts,
)

ALLOWED_REVIEW = frozenset({'pending', 'reviewed', 'verified', 'incorrect'})


@dataclass(frozen=True)
class Candidate:
    id: str
    original: Credential
    name: str
    url: str
    username: str
    password: str
    note: str
    included: bool = True
    review: str = 'pending'

    @classmethod
    def from_source(cls, row: Credential) -> 'Candidate':
        original_android = row.url.lower().startswith('android://')
        preserved_note = (row.note + '\n\n' if row.note else '') + 'URI Android original: ' + row.url if original_android else row.note
        return cls(
            id=secrets.token_hex(12), original=row,
            name=row.name or url_parts(row.url)[1] or 'Acceso sin nombre',
            url=bitwarden_uri(row.url), username=row.username,
            password=row.password, note=preserved_note,
        )


def kind_of(url: str) -> str:
    return 'android' if url.lower().startswith(('androidapp://', 'android://')) else 'web'


def canonical_url(row: Candidate) -> Any:
    # Compare normalized URLs, preserving paths, ports and protocols.
    identity_url = row.url
    # Keep the signed original identity unless the candidate URL was edited.
    if (row.original.url.lower().startswith('android://') and
            row.url == bitwarden_uri(row.original.url)):
        identity_url = row.original.url
    key, _, _, invalid, embedded_auth = url_parts(identity_url)
    return None if invalid or embedded_auth else key


def summarize(row: Candidate) -> dict[str, Any]:
    _, host, http, invalid, embedded = url_parts(row.url)
    return {
        'id': row.id, 'name': row.name, 'url': row.url,
        'username': row.username, 'type': kind_of(row.url),
        'source': row.original.source, 'line': row.original.line,
        'included': row.included, 'review': row.review,
        'http': http, 'invalid_uri': invalid, 'embedded_auth': embedded,
        'host': host,
    }


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
        same_user = len({r.username for r in members}) == 1
        same_password = len({r.password for r in members}) == 1
        category = 'conflict' if conflict else ('exact' if same_user and same_password else 'multiple-accounts')
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
    passwords: dict[str, list[Candidate]] = defaultdict(list)
    weak = []
    incomplete = []
    for r in active:
        if r.password:
            passwords[r.password].append(r)
        if r.password and (len(r.password) < 12 or simple_weak(r.password)):
            weak.append(r.id)
        if not r.url or not r.username or not r.password or url_parts(r.url)[3]:
            incomplete.append(r.id)
    reused = []
    for members in passwords.values():
        accounts = {(canonical_url(r), r.username) for r in members}
        if len(accounts) > 1:
            reused.append([r.id for r in members])
    return {'reused': reused, 'weak': weak, 'incomplete': incomplete, 'breaches': 'not_checked'}


class Workspace:
    """Single-user process-local state; no plaintext is intentionally persisted."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, Candidate] = {}
        self._files: list[dict[str, Any]] = []
        self._history: list[dict[str, Candidate]] = []

    def _checkpoint(self) -> None:
        self._history.append(self._records.copy())
        if len(self._history) > 30:
            self._history.pop(0)

    def import_files(self, files: list[tuple[str, bytes]], repair_extra_notes: bool = False) -> dict[str, Any]:
        """Parse all files or none. The legacy parser requires a filename;
        temporary files are immediately removed even on errors.
        """
        candidates = []
        metadata = []
        for file_name, content in files:
            if b'\x00' in content:
                raise ValueError('Archivo con bytes nulos; se rechaza la importación')
            header = next(csv.reader(io.StringIO(content.decode('utf-8-sig', errors='strict'))), [])
            keys = {h.strip().casefold().replace('_', '') for h in header}
            source = 'firefox' if 'httprealm' in keys else ('brave' if 'brave' in file_name.lower() else 'chrome')
            # A temporary file is necessary until read_export accepts streams.
            # It is deleted immediately and never placed in the project directory.
            tmp_path = None
            try:
                with NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = Path(tmp.name)
                parsed = read_export(source, str(tmp_path), repair_extra_notes=repair_extra_notes)
            finally:
                if tmp_path is not None:
                    tmp_path.unlink(missing_ok=True)
            candidates.extend(Candidate.from_source(row) for row in parsed)
            metadata.append({'name': Path(file_name).name, 'source': source, 'count': len(parsed)})
        if not candidates:
            raise ValueError('No se encontraron credenciales válidas')
        with self._lock:
            self._records = {r.id: r for r in candidates}
            self._files = metadata
            self._history.clear()
            return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            records = list(self._records.values())
            active = [r for r in records if r.included]
            return {
                'files': list(self._files),
                'records': [summarize(r) for r in records],
                'groups': detect_groups(records),
                'audit': detect_audit(records),
                'stats': {
                    'total': len(records), 'included': len(active),
                    'excluded': len(records) - len(active),
                    'reviewed': sum(r.review != 'pending' for r in records),
                    'verified': sum(r.review == 'verified' for r in records),
                },
                'can_undo': bool(self._history),
                'session_saved': False,
            }

    def get(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            row = self._records.get(identifier)
            if row is None:
                raise KeyError(identifier)
            return {**summarize(row), 'password': row.password, 'note': row.note,
                    'original': {'name': row.original.name, 'url': row.original.url,
                                 'username': row.original.username, 'source': row.original.source,
                                 'line': row.original.line}}

    def change(self, identifier: str, changes: dict[str, Any]) -> dict[str, Any]:
        allowed = {'name', 'url', 'username', 'password', 'note', 'included', 'review'}
        if not changes or not set(changes).issubset(allowed):
            raise ValueError('Cambios vacíos o campos no permitidos')
        if 'review' in changes and changes['review'] not in ALLOWED_REVIEW:
            raise ValueError('Estado de revisión no válido')
        with self._lock:
            before = self._records.get(identifier)
            if before is None:
                raise KeyError(identifier)
            updated = replace(before, **changes)
            # Editing identifying/secret fields invalidates previously verified access.
            if any(getattr(before, key) != getattr(updated, key)
                   for key in ('url', 'username', 'password')):
                updated = replace(updated, review='pending')
            if updated == before:
                return self.snapshot()
            self._checkpoint()
            self._records[identifier] = updated
            return self.snapshot()

    def merge_exact(self) -> dict[str, Any]:
        """Explicit, reversible merge only; different passwords never vanish."""
        with self._lock:
            by_identity = defaultdict(list)
            for r in self._records.values():
                if r.included and r.password and r.username:
                    key = canonical_url(r)
                    if key is not None:
                        by_identity[(key, r.username, r.password)].append(r)
            groups = [g for g in by_identity.values() if len(g) > 1]
            if not groups:
                return self.snapshot()
            self._checkpoint()
            for group in groups:
                primary = group[0]
                distinct_notes = list(dict.fromkeys(r.note for r in group if r.note.strip()))
                new_note = '\n\n----- Nota adicional -----\n\n'.join(distinct_notes)
                self._records[primary.id] = replace(primary, note=new_note)
                for r in group[1:]:
                    self._records[r.id] = replace(r, included=False)
            return self.snapshot()

    def undo(self) -> dict[str, Any]:
        with self._lock:
            if not self._history:
                raise ValueError('No hay cambios que deshacer')
            self._records = self._history.pop()
            return self.snapshot()

    def export_csv(self) -> tuple[bytes, int]:
        with self._lock:
            records = [r for r in self._records.values() if r.included]
            if not records:
                raise ValueError('No hay credenciales para exportar')
            buffer = io.StringIO(newline='')
            writer = csv.DictWriter(buffer, fieldnames=BITWARDEN_FIELDS, lineterminator='\n')
            writer.writeheader()
            for row in records:
                writer.writerow({
                    'folder': '', 'favorite': '', 'type': 'login',
                    'name': row.name, 'notes': row.note, 'fields': '',
                    'reprompt': '0', 'login_uri': row.url, 'login_username': row.username,
                    'login_password': row.password, 'login_totp': '',
                })
            return buffer.getvalue().encode('utf-8-sig'), len(records)
