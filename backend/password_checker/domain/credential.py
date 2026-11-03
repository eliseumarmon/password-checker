"""Imported credential value object."""
from __future__ import annotations

from dataclasses import dataclass

from .urls import android_package, parse_url

# Where an export came from: metadata only, it never decides how the CSV is read.
ORIGINS = ("chrome", "brave", "firefox", "safari", "unknown")


@dataclass(frozen=True)
class Credential:
    source: str  # One of ORIGINS; the field keeps its name so .pwc sessions do not change.
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
