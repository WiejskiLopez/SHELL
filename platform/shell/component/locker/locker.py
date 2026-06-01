from __future__ import annotations

from shell.utils.path.path import Path, PathType
from collections.abc import Callable

from shell.component.locker.internal._acquire_locker import _acquire_locker
from shell.component.locker.internal._release_node_dir_lock import release_node_dir_lock
from shell.component.locker.internal._assert_lock_path_set import _assert_lock_path_set


class Locker:
    """Locker manager for a single node run."""

    __slots__ = ("_app", "_lock_path")

    def __init__(self, app) -> None:
        self._app = app
        self._lock_path: str | None = None

    @property
    def lock_path_(self) -> PathType:
        """Return the resolved lock path. Raises if not set."""
        _assert_lock_path_set(self._lock_path)
        return Path.new(self._lock_path).resolve()

    def lock_(self, locker: Callable[[PathType], PathType] | None = None) -> None:
        _acquire_locker(self, acquirer=locker)

    def unlock(self) -> None:
        """Release the node lock stored in lock_path.

        No-op when lock_path is not set (lock was never acquired).
        """
        if not self._lock_path:
            return
        release_node_dir_lock(Path.new(self._lock_path))
