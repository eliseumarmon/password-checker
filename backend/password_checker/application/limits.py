"""Workspace file-count policy and bounds for untrusted session snapshots."""

# Imported files become session metadata, so both paths share this bound.
MAX_WORKSPACE_FILES = 15
MAX_SESSION_RECORDS = 100_000
MAX_SNAPSHOT_TEXT_CHARS = 100_000
MAX_SNAPSHOT_FILE_NAME_CHARS = 1024
