"""Account identity: when two credentials can safely be treated as the same login."""
from __future__ import annotations

from typing import Any, Optional, Tuple

from .credential import Credential
from .urls import parse_url


def host_account(rec: Credential) -> Optional[Tuple[str, str]]:
    """Domain + username, for reuse and relatedness checks across URL paths."""
    url = parse_url(rec.url)
    if url.host and not url.invalid and rec.username:
        return url.host, rec.username
    return None


def account_key(rec: Credential) -> Optional[Any]:
    url = parse_url(rec.url)
    if not rec.url or not rec.username or url.invalid or url.embedded_auth:
        return None  # No fusionar cuentas ambiguas o sin usuario.
    return url.key, rec.username  # No cambiar mayusculas de usuarios potencialmente sensibles.


def duplicate_key(rec: Credential) -> Optional[Any]:
    account = account_key(rec)
    return (account, rec.password) if account and rec.password else None


def masked_username(username: str) -> str:
    if not username:
        return "(sin usuario)"
    if "@" in username:
        local, domain = username.rsplit("@", 1)
        return (local[:2] + "***@" + domain) if local else "***@" + domain
    return username[:2] + "***" if len(username) > 2 else "**"
