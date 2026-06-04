"""_clean_dir.py
Remove all files and subdirectories inside a single directory.
"""
from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_dir(
    target: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all contents of *target* directory (if it exists).

    Does NOT remove the directory itself.
    """
    if not Path.exists(target):
        return
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
