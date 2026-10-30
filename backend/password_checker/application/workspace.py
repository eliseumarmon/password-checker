"""In-memory review workspace: state, undo history and review use cases.

Rules come from the shared domain package, so the CLI and the GUI agree.
No HTTP, file or encryption dependencies: the API adapter reads and writes those.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

from ..domain.accounts import duplicate_key
from ..domain.credential import Credential
from ..domain.notes import combine_notes
from .candidate import ALLOWED_REVIEW, Candidate, identity
from .review_state import detail, review_state
from .session_snapshot import from_payload, to_payload


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

    def import_files(self, files: list[tuple[str, str, list[Credential]]]) -> dict[str, Any]:
        """Replace the workspace with already parsed files: (file name, source, credentials)."""
        candidates = [Candidate.from_source(row) for _, _, rows in files for row in rows]
        metadata = [{'name': Path(file_name).name, 'source': source, 'count': len(rows)}
                    for file_name, source, rows in files]
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
            return review_state(list(self._records.values()), self._files,
                                bool(self._history), self._restored)

    def get(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            row = self._records.get(identifier)
            if row is None:
                raise KeyError(identifier)
            return detail(row)

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
            # Editing identifying/secret fields always invalidates the review, even when
            # the same edit sets one: the new values have not been checked yet.
            if any(getattr(before, key) != getattr(updated, key)
                   for key in ('url', 'username', 'password')):
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
            # Records already in the trash (or repeated ids) need no change and no undo step.
            pending = [i for i in dict.fromkeys(identifiers) if self._records[i].included]
            if not pending:
                return self.snapshot()
            self._checkpoint()
            for identifier in pending:
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
            return to_payload(list(self._records.values()), self._files)

    def restore(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate the entire untrusted snapshot before committing any change."""
        records, files = from_payload(payload)
        with self._lock:
            self._records = records
            self._files = files
            self._history.clear()
            self._restored = True
            return self.snapshot()
