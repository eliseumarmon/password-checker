"""Offline, indicative password strength. Not a cryptographic estimate or breach check."""
from __future__ import annotations

import re
from enum import Enum

MIN_LENGTH = 12
RECOMMENDED_LENGTH = 14
COMMON = frozenset({
    "123456", "12345678", "123456789", "1234567890", "123456789123",
    "password", "password1", "password123", "qwerty", "qwerty123",
    "admin", "admin123", "letmein", "welcome", "welcome1", "abc123",
    "111111", "000000", "iloveyou", "contrasena", "contraseña", "1234",
    "12345", "dragon", "monkey", "123123", "qwertyuiop",
})


class Strength(Enum):
    """Ordered from most to least urgent."""
    EMPTY = "empty"
    OBVIOUS = "obvious"
    SHORT = "short"
    MODERATE = "moderate"
    ACCEPTABLE = "acceptable"


def is_obviously_weak(password: str) -> bool:
    lower = password.casefold()
    return (lower in COMMON or
            bool(re.fullmatch(r"(.)\1{5,}", password)) or
            bool(re.fullmatch(r"(12345|123456|qwerty|asdf|abcd)[a-z0-9]*", lower)))


def assess_strength(password: str) -> Strength:
    if not password:
        return Strength.EMPTY
    if is_obviously_weak(password):
        return Strength.OBVIOUS
    if len(password) < MIN_LENGTH:
        return Strength.SHORT
    if len(password) < RECOMMENDED_LENGTH:
        return Strength.MODERATE
    return Strength.ACCEPTABLE


def is_weak(password: str) -> bool:
    return assess_strength(password) in (Strength.OBVIOUS, Strength.SHORT)
