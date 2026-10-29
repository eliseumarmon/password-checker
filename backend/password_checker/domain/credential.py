"""Imported credential value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Credential:
    source: str
    line: int
    name: str
    url: str
    username: str
    password: str
    note: str
