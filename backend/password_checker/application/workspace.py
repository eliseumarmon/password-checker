"""In-memory review workspace: state, undo history and review use cases.

Rules come from the domain package.
No HTTP, file or encryption dependencies: the API adapter reads and writes those.
"""
from __future__ import annotations

import threading
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any, Sequence

from ..domain.accounts import duplicate_key
from ..domain.credential import ORIGINS, Credential
from ..domain.notes import combine_notes
from . import limits
from .candidate import ALLOWED_REVIEW, Candidate, identity, merged_totp
from .review_state import detail, review_state
from .session_snapshot import from_payload, session_fit, to_payload


@dataclass(frozen=True, kw_only=True)
class ImportedFile:
    """Complete parsed file; the caller supplies a valid base name."""

    name: str
    source: str
    credentials: Sequence[Credential]

    def __post_init__(self) -> None:
        if (not isinstance(self.name, str) or not self.name.strip()
                or self.name in ('.', '..') or '/' in self.name or '\\' in self.name
                or len(self.name) > limits.MAX_SNAPSHOT_FILE_NAME_CHARS
                or any(unicodedata.category(char) == 'Cc' for char in self.name)):
            raise ValueError('Nombre de archivo no válido')
        if self.source not in ORIGINS:
            raise ValueError('Origen de archivo no válido')
        object.__setattr__(self, 'credentials', tuple(self.credentials))


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

    def _ensure_restorable(self, records: dict[str, Candidate], files: list[dict[str, Any]], *,
                           allow_reduction: bool = True) -> None:
        """Refuse a new state that could not be saved to a session file and opened again.

        Once over a limit, a change that does not make the excess worse is still accepted,
        so the user can fix it; a rejected one names the measure it made worse.
        """
        fit = session_fit(list(records.values()), files)
        problem = fit.problem
        if problem is not None and allow_reduction:
            problem = fit.worsened(session_fit(list(self._records.values()), self._files))
        if problem is not None:
            raise ValueError(problem)

    def import_files(self, files: list[ImportedFile]) -> dict[str, Any]:
        """Replace the workspace with already parsed files."""
        candidates = [Candidate.from_source(row) for file in files for row in file.credentials]
        metadata = [{'name': file.name, 'source': file.source, 'count': len(file.credentials)}
                    for file in files]
        if not candidates:
            raise ValueError('No se encontraron credenciales válidas')
        records = {r.id: r for r in candidates}
        with self._lock:
            self._ensure_restorable(records, metadata, allow_reduction=False)
            self._records = records
            self._files = metadata
            self._history.clear()
            return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return review_state(list(self._records.values()), self._files,
                                bool(self._history))

    def get(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            row = self._records.get(identifier)
            if row is None:
                raise KeyError(identifier)
            return detail(row)

    def change(self, identifier: str, changes: dict[str, Any]) -> dict[str, Any]:
        allowed = {'name', 'url', 'username', 'password', 'note', 'totp', 'included', 'review'}
        if not changes or not set(changes).issubset(allowed):
            raise ValueError('Cambios vacíos o campos no permitidos')
        if 'review' in changes and changes['review'] not in ALLOWED_REVIEW:
            raise ValueError('Estado de revisión no válido')
        with self._lock:
            before = self._records.get(identifier)
            if before is None:
                raise KeyError(identifier)
            updated = replace(before, **changes)
            # Editing identifying/secret fields always invalidates the review, even when
            # the same edit sets one: the new values have not been checked yet.
            if any(getattr(before, key) != getattr(updated, key)
                   for key in ('url', 'username', 'password', 'totp')):
                updated = replace(updated, review='pending')
            if updated == before:
                return self.snapshot()
            records = {**self._records, identifier: updated}
            self._ensure_restorable(records, self._files)
            self._checkpoint()
            self._records = records
            return self.snapshot()

    def trash(self, identifiers: list[str]) -> dict[str, Any]:
        """Move several records to the trash all at once, as one undo step."""
        # The HTTP model rejects empty batches; direct application callers need this guard too.
        if not identifiers:
            raise ValueError('No hay credenciales que mover a la papelera')
        with self._lock:
            missing = [i for i in identifiers if i not in self._records]
            if missing:
                raise KeyError(missing[0])
            # Records already in the trash (or repeated ids) need no change and no undo step.
            pending = [i for i in dict.fromkeys(identifiers) if self._records[i].included]
            if not pending:
                return self.snapshot()
            records = {**self._records, **{i: replace(self._records[i], included=False) for i in pending}}
            self._ensure_restorable(records, self._files)
            self._checkpoint()
            self._records = records
            return self.snapshot()

    def merge_exact(self) -> dict[str, Any]:
        """Explicit, reversible merge only; different passwords never vanish."""
        with self._lock:
            by_identity = defaultdict(list)
            for r in self._records.values():
                key = duplicate_key(identity(r)) if r.included else None
                if key is not None:
                    by_identity[key].append(r)
            # Copies with two different TOTPs are not exact copies (S6): none of them merges.
            groups = [(g, merged_totp(g)) for g in by_identity.values() if len(g) > 1]
            groups = [(g, totp) for g, totp in groups if totp is not None]
            if not groups:
                return self.snapshot()
            records = dict(self._records)
            for group, totp in groups:
                primary = group[0]
                # A secret the kept record did not have has not been checked yet, as in change().
                review = primary.review if primary.totp == totp else 'pending'
                records[primary.id] = replace(primary, note=combine_notes(r.note for r in group),
                                              totp=totp, review=review)
                for r in group[1:]:
                    records[r.id] = replace(r, included=False)
            self._ensure_restorable(records, self._files)
            self._checkpoint()
            self._records = records
            return self.snapshot()

    def undo(self) -> dict[str, Any]:
        with self._lock:
            if not self._history:
                raise ValueError('No hay cambios que deshacer')
            self._records = self._history.pop()
            return self.snapshot()

    def export_records(self) -> list[Candidate]:
        with self._lock:
            records = [r for r in self._records.values() if r.included]
            if not records:
                raise ValueError('No hay credenciales para exportar')
            return records

    def serialize(self) -> dict[str, Any]:
        """Copy the full candidate state for encryption without writing plaintext."""
        with self._lock:
            if not self._records:
                raise ValueError('No hay ninguna sesión cargada')
            payload = to_payload(list(self._records.values()), self._files)
            # Defensive: never hand out a snapshot that restore() would reject.
            from_payload(payload)
            return payload

    def restore(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate the entire untrusted snapshot before committing any change."""
        records, files = from_payload(payload)
        with self._lock:
            self._ensure_restorable(records, files, allow_reduction=False)
            self._records = records
            self._files = files
            self._history.clear()
            return self.snapshot()
