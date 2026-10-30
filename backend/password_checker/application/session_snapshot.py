"""Session state as plain data for encryption, and strict validation when it comes back."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..domain.credential import Credential
from .candidate import ALLOWED_REVIEW, Candidate


def to_payload(records: list[Candidate], files: list[dict[str, Any]]) -> dict[str, Any]:
    return {'version': 1, 'files': list(files), 'records': [asdict(row) for row in records]}


def from_payload(payload: dict[str, Any]) -> tuple[dict[str, Candidate], list[dict[str, Any]]]:
    """Validate the entire untrusted snapshot; return (records by id, file metadata)."""
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
    return validated, safe_files
