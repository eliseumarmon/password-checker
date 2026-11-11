"""Session state as plain data for encryption, and strict validation when it comes back."""
from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from typing import Any

from ..domain.credential import ORIGINS, Credential
from . import limits
from .candidate import ALLOWED_REVIEW, RETIRED_REVIEW, Candidate

FIELD_LABELS = {'name': 'nombre', 'url': 'URL', 'username': 'usuario', 'password': 'contraseña', 'note': 'notas',
                'totp': 'TOTP'}
# v2 adds the TOTP to the original and the candidate; v1 files are refused, never migrated.
SESSION_VERSION = 2


def to_payload(records: list[Candidate], files: list[dict[str, Any]]) -> dict[str, Any]:
    return {'version': SESSION_VERSION, 'files': list(files), 'records': [asdict(row) for row in records]}


def encode_payload(payload: dict[str, Any]) -> bytes:
    """The exact plaintext a session file encrypts."""
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def describe_size(size: int) -> str:
    unit, scale = ('MiB', 1024 * 1024) if size >= 1024 * 1024 else ('KiB', 1024)
    return f'{size / scale:.1f} {unit}'.replace('.', ',')


def _oversized_fields(records: Iterable[Candidate]) -> Iterator[tuple[tuple[str, str], str, int]]:
    """Each field over the text limit: which one it is (record id and field), a message naming it
    and its source line, never its value, and how many characters it has too many."""
    for row in records:
        for key, label in FIELD_LABELS.items():
            for value, suffix in ((getattr(row, key), ''), (getattr(row.original, key), ' original')):
                if len(value) > limits.MAX_SNAPSHOT_TEXT_CHARS:
                    message = (f'El campo «{label}{suffix}» de la credencial de {row.original.source}, '
                               f'línea {row.original.line}, supera los {limits.MAX_SNAPSHOT_TEXT_CHARS} '
                               'caracteres que admite una sesión cifrada.')
                    yield (row.id, key + suffix), message, len(value) - limits.MAX_SNAPSHOT_TEXT_CHARS


@dataclass(frozen=True)
class SessionFit:
    """How a workspace state measures against what a session file can save and restore."""

    records: int
    files: int
    oversized_fields: tuple[tuple[tuple[str, str], str, int], ...]
    excess_chars: int
    file_bytes: int

    @property
    def problem(self) -> str | None:
        """The first limit exceeded, in a fixed order: records, files, characters, size."""
        return self._first_problem(None)

    def worsened(self, before: SessionFit) -> str | None:
        """The first measure that grows past its limit and past where *before* already was."""
        return self._first_problem(before)

    def _first_problem(self, before: SessionFit | None) -> str | None:
        def grows(new: int, old: int, limit: int) -> bool:
            return new > (limit if before is None else max(old, limit))

        base = before or self
        if grows(self.records, base.records, limits.MAX_SESSION_RECORDS):
            return (f'Una sesión cifrada admite como máximo {limits.MAX_SESSION_RECORDS} credenciales '
                    f'y el resultado tendría {self.records}.')
        if grows(self.files, base.files, limits.MAX_WORKSPACE_FILES):
            return (f'Una sesión cifrada admite como máximo {limits.MAX_WORKSPACE_FILES} archivos '
                    f'y el resultado tendría {self.files}.')
        if grows(self.excess_chars, base.excess_chars, 0):
            # The first field whose excess grew is one the change touched; the total grew, so one did.
            excess_before = {field: excess for field, _, excess in before.oversized_fields} if before is not None else {}
            return next(message for field, message, excess in self.oversized_fields
                        if excess > excess_before.get(field, 0))
        if grows(self.file_bytes, base.file_bytes, limits.MAX_SESSION_BYTES):
            return (f'El resultado no cabe en una sesión cifrada: ocuparía {describe_size(self.file_bytes)} '
                    f'y el máximo es {describe_size(limits.MAX_SESSION_BYTES)}.')
        return None


def session_fit(records: list[Candidate], files: list[dict[str, Any]]) -> SessionFit:
    oversized = list(_oversized_fields(records))
    return SessionFit(len(records), len(files), tuple(oversized),
                      sum(excess for _, _, excess in oversized),
                      limits.session_file_size(len(encode_payload(to_payload(records, files)))))


def from_payload(payload: dict[str, Any]) -> tuple[dict[str, Candidate], list[dict[str, Any]]]:
    """Validate the entire untrusted snapshot; return (records by id, file metadata)."""
    if payload.get('version') == 1:
        raise ValueError('Esta sesión es de una versión anterior y ya no se puede abrir: vuelve a importar los CSV.')
    if payload.get('version') != SESSION_VERSION or not isinstance(payload.get('records'), list):
        raise ValueError('Formato de sesión no compatible')
    items = payload['records']
    if not 1 <= len(items) <= limits.MAX_SESSION_RECORDS:
        raise ValueError('Número de credenciales no válido')
    files = payload.get('files')
    if not isinstance(files, list) or len(files) > limits.MAX_WORKSPACE_FILES:
        raise ValueError('Metadatos de sesión no válidos')
    validated = {}
    expected = {'id', 'original', 'name', 'url', 'username', 'password', 'note', 'totp', 'included', 'review'}
    original_keys = {'source', 'line', 'name', 'url', 'username', 'password', 'note', 'totp'}
    for raw in items:
        if not isinstance(raw, dict) or set(raw) != expected or not isinstance(raw.get('original'), dict):
            raise ValueError('Credencial cifrada no válida')
        origin = raw['original']
        if set(origin) != original_keys:
            raise ValueError('Origen de credencial no válido')
        for key in ('source', 'name', 'url', 'username', 'password', 'note', 'totp'):
            if not isinstance(origin[key], str) or len(origin[key]) > limits.MAX_SNAPSHOT_TEXT_CHARS:
                raise ValueError('Datos de origen no válidos')
        if type(origin['line']) is not int or origin['line'] < 1:
            raise ValueError('Línea de origen no válida')
        for key in ('id', 'name', 'url', 'username', 'password', 'note', 'totp'):
            if not isinstance(raw[key], str) or len(raw[key]) > limits.MAX_SNAPSHOT_TEXT_CHARS:
                raise ValueError('Campo de credencial no válido')
        if not raw['id'] or raw['id'] in validated or not isinstance(raw['included'], bool):
            raise ValueError('ID o inclusión de credencial no válidos')
        review = RETIRED_REVIEW.get(raw['review'], raw['review']) if isinstance(raw['review'], str) else None
        if review not in ALLOWED_REVIEW:
            raise ValueError('Estado de revisión no válido')
        validated[raw['id']] = Candidate(
            id=raw['id'], original=Credential(**origin),
            name=raw['name'], url=raw['url'], username=raw['username'],
            password=raw['password'], note=raw['note'], totp=raw['totp'],
            included=raw['included'], review=review,
        )
    safe_files = []
    for file in files:
        if (not isinstance(file, dict) or set(file) != {'name', 'source', 'count'}
                or not isinstance(file['name'], str) or len(file['name']) > limits.MAX_SNAPSHOT_FILE_NAME_CHARS
                or file['source'] not in ORIGINS
                or type(file['count']) is not int or file['count'] < 0):
            raise ValueError('Metadatos de archivo no válidos')
        safe_files.append(file)
    return validated, safe_files
