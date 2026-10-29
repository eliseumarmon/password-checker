"""Bitwarden (csv) export format. Output contains plaintext passwords."""
from __future__ import annotations

import csv
from typing import Dict, Iterable, Protocol, TextIO

BITWARDEN_FIELDS = (
    "folder", "favorite", "type", "name", "notes", "fields", "reprompt",
    "login_uri", "login_username", "login_password", "login_totp",
)


class LoginRecord(Protocol):
    name: str
    url: str
    username: str
    password: str
    note: str


def bitwarden_row(item: LoginRecord) -> Dict[str, str]:
    return {
        "folder": "", "favorite": "", "type": "login",
        "name": item.name, "notes": item.note, "fields": "",
        "reprompt": "0", "login_uri": item.url,
        "login_username": item.username,
        "login_password": item.password, "login_totp": "",
    }


def write_bitwarden_csv(file: TextIO, items: Iterable[LoginRecord]) -> int:
    """Write header and rows; return the number of credentials written."""
    writer = csv.DictWriter(file, fieldnames=BITWARDEN_FIELDS, lineterminator="\n")
    writer.writeheader()
    count = 0
    for item in items:
        writer.writerow(bitwarden_row(item))
        count += 1
    return count
