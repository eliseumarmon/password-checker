"""Workspace and session bounds: one place, so every accepted state can be saved and restored.

Read them as ``limits.NAME`` at call time, never copied into another module.
"""

# Imported files become session metadata, so both paths share this bound.
MAX_WORKSPACE_FILES = 15
MAX_SESSION_RECORDS = 100_000
MAX_SNAPSHOT_TEXT_CHARS = 100_000
MAX_SNAPSHOT_FILE_NAME_CHARS = 1024
MAX_SESSION_BYTES = 25 * 1024 * 1024

# The .pwc envelope around base64(ciphertext): fixed JSON keys, salt and nonce.
# Pinned against infrastructure.sessions by tests/test_session_limits.py.
SESSION_ENVELOPE_BYTES = 132
SESSION_AEAD_TAG_BYTES = 16


def session_file_size(plaintext_bytes: int) -> int:
    """Exact size of the .pwc file that encrypts a payload of *plaintext_bytes*."""
    return SESSION_ENVELOPE_BYTES + 4 * -(-(plaintext_bytes + SESSION_AEAD_TAG_BYTES) // 3)
