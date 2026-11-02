"""Session state as plain data for encryption, and strict validation when it comes back."""
from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from typing import Any

from ..domain.credential import BROWSER_SOURCES, Credential
from . import limits
from .candidate import ALLOWED_REVIEW, Candidate

FIELD_LABELS = {'name': 'nombre', 'url': 'URL', 'username': 'usuario', 'password': 'contraseña', 'note': 'notas'}


def to_payload(records: list[Candidate], files: list[dict[str, Any]]) -> dict[str, Any]:
    return {'version': 1, 'files': list(files), 'records': [asdict(row) for row in records]}


def encode_payload(payload: dict[str, Any]) -> bytes:
    """The exact plaintext a session file encrypts."""
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def describe_size(size: int) -> str:
    unit, scale = ('MiB', 1024 * 1024) if size >= 1024 * 1024 else ('KiB', 1024)
    return f'{size / scale:.1f} {unit}'.replace('.', ',')


def _oversized_fields(records: Iterable[Candidate]) -> Iterator[str]:
    """Name the field and its source line, never its value."""
    for row in records:
        for key, label in FIELD_LABELS.items():
            for value, suffix in ((getattr(row, key), ''), (getattr(row.original, key), ' original')):
                if len(value) > limits.MAX_SNAPSHOT_TEXT_CHARS:
                    yield (f'El campo «{label}{suffix}» de la credencial de {row.original.source}, '
                           f'línea {row.original.line}, supera los {limits.MAX_SNAPSHOT_TEXT_CHARS} '
                           'caracteres que admite una sesión cifrada.')


@dataclass(frozen=True)
class SessionFit:
    """How a workspace state measures against what a session file can save and restore."""

    records: int
    oversized_fields: tuple[str, ...]
    file_bytes: int

    @property
    def problem(self) -> str | None:
        if self.records > limits.MAX_SESSION_RECORDS:
            return (f'Una sesión cifrada admite como máximo {limits.MAX_SESSION_RECORDS} credenciales '
                    f'y el resultado tendría {self.records}.')
        if self.oversized_fields:
            return self.oversized_fields[0]
        if self.file_bytes > limits.MAX_SESSION_BYTES:
            return (f'El resultado no cabe en una sesión cifrada: ocuparía {describe_size(self.file_bytes)} '
                    f'y el máximo es {describe_size(limits.MAX_SESSION_BYTES)}.')
        return None

    def no_worse_than(self, other: SessionFit) -> bool:
        return (self.records <= other.records
                and len(self.oversized_fields) <= len(other.oversized_fields)
                and self.file_bytes <= other.file_bytes)


def session_fit(records: list[Candidate], files: list[dict[str, Any]]) -> SessionFit:
    return SessionFit(len(records), tuple(_oversized_fields(records)),
                      limits.session_file_size(len(encode_payload(to_payload(records, files)))))


def from_payload(payload: dict[str, Any]) -> tuple[dict[str, Candidate], list[dict[str, Any]]]:
    """Validate the entire untrusted snapshot; return (records by id, file metadata)."""
    if payload.get('version') != 1 or not isinstance(payload.get('records'), list):
        raise ValueError('Formato de sesión no compatible')
    items = payload['records']
    if not 1 <= len(items) <= limits.MAX_SESSION_RECORDS:
        raise ValueError('Número de credenciales no válido')
    files = payload.get('files')
    if not isinstance(files, list) or len(files) > limits.MAX_WORKSPACE_FILES:
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
            if not isinstance(origin[key], str) or len(origin[key]) > limits.MAX_SNAPSHOT_TEXT_CHARS:
                raise ValueError('Datos de origen no válidos')
        if type(origin['line']) is not int or origin['line'] < 1:
            raise ValueError('Línea de origen no válida')
        for key in ('id', 'name', 'url', 'username', 'password', 'note'):
            if not isinstance(raw[key], str) or len(raw[key]) > limits.MAX_SNAPSHOT_TEXT_CHARS:
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
                or not isinstance(file['name'], str) or len(file['name']) > limits.MAX_SNAPSHOT_FILE_NAME_CHARS
                or file['source'] not in BROWSER_SOURCES
                or type(file['count']) is not int or file['count'] < 0):
            raise ValueError('Metadatos de archivo no válidos')
        safe_files.append(file)
    return validated, safe_files
