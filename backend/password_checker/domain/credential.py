"""Imported credential value object."""
from __future__ import annotations

from dataclasses import dataclass

from .urls import android_package, parse_url


@dataclass(frozen=True)
class Credential:
    source: str
    line: int
    name: str
    url: str
    username: str
    password: str
    note: str


def display_name(name: str, url: str) -> str:
    """Blank names fall back to the Android package, the domain or a placeholder."""
    if name.strip():
        return name
    return android_package(url) or parse_url(url).host or "Acceso sin nombre"
