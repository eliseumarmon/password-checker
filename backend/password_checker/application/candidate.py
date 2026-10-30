"""Editable review record. Original credentials are immutable; edits never change imports."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, replace

from ..domain.credential import Credential, display_name
from ..domain.urls import bitwarden_uri

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
            name=display_name(row.name, row.url),
            url=bitwarden_uri(row.url), username=row.username,
            password=row.password, note=row.note,
        )


def identity(row: Candidate) -> Credential:
    """The edited record as the domain sees it, for the shared duplicate rules."""
    url = row.url
    # Keep the signed original identity unless the candidate URL was edited.
    if (row.original.url.lower().startswith('android://') and
            row.url == bitwarden_uri(row.original.url)):
        url = row.original.url
    return replace(row.original, url=url, username=row.username, password=row.password)
