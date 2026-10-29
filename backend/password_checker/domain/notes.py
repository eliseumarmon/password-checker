"""Note merging: distinct notes are always preserved, never silently dropped."""
from __future__ import annotations

from typing import Iterable

NOTE_SEPARATOR = "\n\n----- Nota adicional -----\n\n"


def combine_notes(notes: Iterable[str]) -> str:
    return NOTE_SEPARATOR.join(dict.fromkeys(note for note in notes if note.strip()))
