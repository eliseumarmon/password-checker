"""In-memory review workspace. No HTTP or UI dependencies.

Rules come from the shared domain package, so the CLI and the GUI agree.
Original credentials are immutable; candidate edits never change imports.
"""
from __future__ import annotations

import csv
import io
import secrets
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .domain.accounts import duplicate_key
from .domain.credential import Credential
from .domain.notes import combine_notes
from .domain.reuse import reused_password_groups
from .domain.strength import is_weak
from .domain.urls import android_package, bitwarden_uri, parse_url
from .infrastructure.bitwarden import write_bitwarden_csv
from .infrastructure.csv_reader import read_export

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
        # The original android:// URI stays in `original`; the export follows Bitwarden.
        return cls(
            id=secrets.token_hex(12), original=row,
            name=row.name or android_package(row.url) or parse_url(row.url).host or 'Acceso sin nombre',
            url=bitwarden_uri(row.url), username=row.username,
            password=row.password, note=row.note,
        )


def kind_of(url: str) -> str:
    return 'android' if url.lower().startswith(('androidapp://', 'android://')) else 'web'


def identity(row: Candidate) -> Credential:
    """The edited record as the domain sees it, for the shared duplicate rules."""
    url = row.url
    # Keep the signed original identity unless the candidate URL was edited.
    if (row.original.url.lower().startswith('android://') and
            row.url == bitwarden_uri(row.original.url)):
        url = row.original.url
    return replace(row.original, url=url, username=row.username, password=row.password)


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


class Workspace:
    """Single-user process-local state; no plaintext is intentionally persisted."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, Candidate] = {}
        self._files: list[dict[str, Any]] = []
        self._history: list[dict[str, Candidate]] = []
        self._restored = False

    def _checkpoint(self) -> None:
        self._history.append(self._records.copy())
        if len(self._history) > 30:
            self._history.pop(0)

    def import_files(self, files: list[tuple[str, bytes]], repair_extra_notes: bool = False) -> dict[str, Any]:
        """Parse all files or none, from memory: no plaintext temporary files."""
        candidates = []
        metadata = []
        for file_name, content in files:
            if b'\x00' in content:
                raise ValueError('Archivo con bytes nulos; se rechaza la importación')
            header = next(csv.reader(io.StringIO(content.decode('utf-8-sig', errors='strict'))), [])
            keys = {h.strip().casefold().replace('_', '') for h in header}
            source = 'firefox' if 'httprealm' in keys else ('brave' if 'brave' in file_name.lower() else 'chrome')
            # Parse directly from a Unicode stream: no explicit plaintext temp file.
            stream = io.StringIO(content.decode('utf-8-sig', errors='strict'), newline='')
            parsed = read_export(source, stream, repair_extra_notes=repair_extra_notes)
            candidates.extend(Candidate.from_source(row) for row in parsed)
            metadata.append({'name': Path(file_name).name, 'source': source, 'count': len(parsed)})
        if not candidates:
            raise ValueError('No se encontraron credenciales válidas')
        with self._lock:
            self._records = {r.id: r for r in candidates}
            self._files = metadata
            self._history.clear()
            self._restored = False
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
                'session_saved': self._restored,
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
            # Editing identifying/secret fields invalidates previously verified access,
            # unless the same edit explicitly sets a new review state.
            if (updated.review == before.review and
                    any(getattr(before, key) != getattr(updated, key)
                        for key in ('url', 'username', 'password'))):
                updated = replace(updated, review='pending')
            if updated == before:
                return self.snapshot()
            self._checkpoint()
            self._records[identifier] = updated
            return self.snapshot()

    def trash(self, identifiers: list[str]) -> dict[str, Any]:
        """Move several records to the trash all at once, as one undo step."""
        if not identifiers:
            raise ValueError('No hay credenciales que mover a la papelera')
        with self._lock:
            missing = [i for i in identifiers if i not in self._records]
            if missing:
                raise KeyError(missing[0])
            self._checkpoint()
            for identifier in identifiers:
                self._records[identifier] = replace(self._records[identifier], included=False)
            return self.snapshot()

    def merge_exact(self) -> dict[str, Any]:
        """Explicit, reversible merge only; different passwords never vanish."""
        with self._lock:
            by_identity = defaultdict(list)
            for r in self._records.values():
                key = duplicate_key(identity(r)) if r.included else None
                if key is not None:
                    by_identity[key].append(r)
            groups = [g for g in by_identity.values() if len(g) > 1]
            if not groups:
                return self.snapshot()
            self._checkpoint()
            for group in groups:
                primary = group[0]
                self._records[primary.id] = replace(primary, note=combine_notes(r.note for r in group))
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
            count = write_bitwarden_csv(buffer, records)
            return buffer.getvalue().encode('utf-8-sig'), count

    def serialize(self) -> dict[str, Any]:
        """Copy the full candidate state for encryption without writing plaintext."""
        with self._lock:
            if not self._records:
                raise ValueError('No hay ninguna sesión cargada')
            return {'version': 1, 'files': list(self._files),
                    'records': [asdict(row) for row in self._records.values()]}

    def restore(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate the entire untrusted snapshot before committing any change."""
        if payload.get('version') != 1 or not isinstance(payload.get('records'), list):
            raise ValueError('Formato de sesión no compatible')
        items = payload['records']
        if not 1 <= len(items) <= 100000:
            raise ValueError('Número de credenciales no válido')
        files = payload.get('files')
        if not isinstance(files, list) or len(files) > 15:
            raise ValueError('Metadatos de sesión no válidos')
        validated = {}
        expected = {'id', 'original', 'name', 'url', 'username', 'password', 'note', 'included', 'review'}
        original_keys = {'source', 'line', 'name', 'url', 'username', 'password', 'note'}
        for raw in items:
            if not isinstance(raw, dict) or set(raw) != expected or not isinstance(raw.get('original'), dict):
                raise ValueError('Credencial cifrada no válida')
            origin = raw['original']
            if set(origin) != original_keys:
                raise ValueError('Origen de credencial no válido')
            for key in ('source', 'name', 'url', 'username', 'password', 'note'):
                if not isinstance(origin[key], str) or len(origin[key]) > 100_000:
                    raise ValueError('Datos de origen no válidos')
            if type(origin['line']) is not int or origin['line'] < 1:
                raise ValueError('Línea de origen no válida')
            for key in ('id', 'name', 'url', 'username', 'password', 'note'):
                if not isinstance(raw[key], str) or len(raw[key]) > 100_000:
                    raise ValueError('Campo de credencial no válido')
            if not raw['id'] or raw['id'] in validated or not isinstance(raw['included'], bool):
                raise ValueError('ID o inclusión de credencial no válidos')
            if not isinstance(raw['review'], str) or raw['review'] not in ALLOWED_REVIEW:
                raise ValueError('Estado de revisión no válido')
            validated[raw['id']] = Candidate(
                id=raw['id'], original=Credential(**origin),
                name=raw['name'], url=raw['url'], username=raw['username'],
                password=raw['password'], note=raw['note'],
                included=raw['included'], review=raw['review'],
            )
        safe_files = []
        for file in files:
            if (not isinstance(file, dict) or set(file) != {'name', 'source', 'count'}
                    or not isinstance(file['name'], str) or len(file['name']) > 1024
                    or file['source'] not in ('chrome', 'brave', 'firefox')
                    or type(file['count']) is not int or file['count'] < 0):
                raise ValueError('Metadatos de archivo no válidos')
            safe_files.append(file)
        with self._lock:
            self._records = validated
            self._files = safe_files
            self._history.clear()
            self._restored = True
            return self.snapshot()
