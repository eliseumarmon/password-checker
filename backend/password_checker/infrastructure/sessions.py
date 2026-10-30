"""Versioned authenticated, encrypted workspace snapshots.

KDF: Argon2id (fixed 64 MiB, 3 passes, 1 lane). AEAD: AES-256-GCM.
Never persist passphrases, keys or decrypted files.
"""
from __future__ import annotations

import base64
import binascii
import json
import secrets
from typing import Any

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSION = 1
AAD = b'password-checker/workspace/session-v1'
MAX_SESSION_BYTES = 25 * 1024 * 1024


def _key(passphrase: str, salt: bytes) -> bytes:
    if not 12 <= len(passphrase) <= 1024:
        raise ValueError('La contraseña de la sesión debe tener entre 12 y 1024 caracteres')
    return hash_secret_raw(
        secret=passphrase.encode('utf-8'), salt=salt,
        time_cost=3, memory_cost=65536, parallelism=1,
        hash_len=32, type=Type.ID,
    )


def _decode(text: Any, expected_size: int | None = None) -> bytes:
    if not isinstance(text, str):
        raise ValueError('Formato cifrado no válido')
    try:
        data = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError('Formato cifrado no válido') from error
    if expected_size is not None and len(data) != expected_size:
        raise ValueError('Formato cifrado no válido')
    return data


def encrypt_session(payload: dict[str, Any], passphrase: str) -> bytes:
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    key = _key(passphrase, salt)
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, AAD)
    document = {'version': VERSION, 'kdf': 'argon2id-64m-3-1', 'cipher': 'aes-256-gcm',
                'salt': base64.b64encode(salt).decode('ascii'),
                'nonce': base64.b64encode(nonce).decode('ascii'),
                'data': base64.b64encode(ciphertext).decode('ascii')}
    return json.dumps(document, separators=(',', ':')).encode('ascii')


def decrypt_session(blob: bytes, passphrase: str) -> dict[str, Any]:
    if not blob or len(blob) > MAX_SESSION_BYTES:
        raise ValueError('Tamaño de sesión no válido')
    try:
        envelope = json.loads(blob)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('Archivo de sesión no válido') from error
    if not isinstance(envelope, dict) or envelope.get('version') != VERSION:
        raise ValueError('Versión de sesión no compatible')
    if envelope.get('kdf') != 'argon2id-64m-3-1' or envelope.get('cipher') != 'aes-256-gcm':
        raise ValueError('Algoritmo de sesión no compatible')
    salt = _decode(envelope.get('salt'), 16)
    nonce = _decode(envelope.get('nonce'), 12)
    ciphertext = _decode(envelope.get('data'))
    try:
        decrypted = AESGCM(_key(passphrase, salt)).decrypt(nonce, ciphertext, AAD)
        result = json.loads(decrypted)
    except (InvalidTag, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('Contraseña incorrecta o archivo de sesión dañado') from error
    if not isinstance(result, dict):
        raise ValueError('Contenido de sesión no válido')
    return result
