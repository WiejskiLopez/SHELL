"""_clean_input.py
Responsible for one thing: removing all contents of the input/ directory inside a node.
"""

from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_input(
    node: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all files and subdirectories inside <node>/input/."""
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    target = node / ".node" / "input"
    if not Path.exists(target):
        return
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
