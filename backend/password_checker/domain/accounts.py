"""Account identity: when two credentials can safely be treated as the same login."""
from __future__ import annotations

from typing import Any, Optional, Tuple

from .credential import Credential
from .urls import parse_url


def origin_account(rec: Credential) -> Optional[Tuple[Any, str]]:
    """Origin (scheme, host, port) or Android package + username: one account for reuse checks.

    Paths of one site are the same account; local apps on different ports are not.
    """
    url = parse_url(rec.url)
    if url.invalid or not rec.username:
        return None
    if url.key[0] in ("android-source", "androidapp"):
        return ("android", url.host), rec.username
    return url.key[:2], rec.username


def account_key(rec: Credential) -> Optional[Any]:
    url = parse_url(rec.url)
    if not rec.url or not rec.username or url.invalid or url.embedded_auth:
        return None  # No fusionar cuentas ambiguas o sin usuario.
    return url.key, rec.username  # No cambiar mayusculas de usuarios potencialmente sensibles.


def duplicate_key(rec: Credential) -> Optional[Any]:
    account = account_key(rec)
    return (account, rec.password) if account and rec.password else None
