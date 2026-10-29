"""Private, exclusive file creation: never overwrites and never follows symlinks."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable, TextIO


def create_new_file(path, protected: Iterable, write: Callable[[TextIO], None], *,
                    same_as_protected_error: str, missing_folder_error: str,
                    newline: str) -> Path:
    """Create *path* with mode 0600 and fill it with *write*.

    *protected* are paths (the inputs) the new file must never replace.
    *missing_folder_error* may contain one ``{}`` for the parent folder.
    A partially written file is removed before the error propagates.
    """
    output = Path(path)
    if any(output.resolve() == Path(filename).resolve() for filename in protected):
        raise ValueError(same_as_protected_error)
    if not output.parent.is_dir():
        raise ValueError(missing_folder_error.format(output.parent))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(output, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as file:
            write(file)
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return output
