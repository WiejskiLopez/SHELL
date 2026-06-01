"""release_lock.py
Responsible for one thing: releasing (deleting) the node lock file.
Safe to call even when the file has already been removed.
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from collections.abc import Callable


def release_node_dir_lock(
    lock_path: PathType,
    remover: Callable[[PathType], None] | None = None,
) -> None:
    """Delete lock_path (best-effort, never raises).

    remover: optional callable (path: PathType) -> None for testability.
    """
    if remover is None:
        remover = Path.unlink
    try:
        remover(lock_path)
    except FileNotFoundError:
        pass
    except OSError:
        pass
