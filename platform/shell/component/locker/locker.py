"""locker.py
Locker: single entry point for acquiring and releasing the node directory lock.

    lock(locker=None)   — acquire exclusive lock, store path in app
    unlock()            — release lock stored in app (no-op if never acquired)
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from collections.abc import Callable

from shell.component.locker.internal._acquire_node_dir_lock import acquire_node_dir_lock
from shell.component.locker.internal._release_node_dir_lock import release_node_dir_lock
from shell.component.locker.internal._lock_error import LockError
from shell.component.locker.internal._assert_lock_path_set import _assert_lock_path_set
from shell.component.result.result import Result


class Locker:
    """Locker manager for a single node run."""

    __slots__ = ("_app", "_lock_path")

    def __init__(self, app) -> None:
        self._app = app
        self._lock_path: str | None = None

    # -----------------------------------------------------------------------
    # Validated property
    # -----------------------------------------------------------------------

    @property
    def lock_path_(self) -> PathType:
        """Return the resolved lock path. Raises if not set."""
        _assert_lock_path_set(self._lock_path)
        return Path.new(self._lock_path).resolve()

    def lock_(self, locker: Callable[[PathType], PathType] | None = None) -> None:
        """Acquire exclusive file lock on the node directory.

        Stores lock path in app lock_path.
        On LockError sets status to 'locked', logs the error, and re-raises.
        locker: optional callable (node: PathType) -> PathType for testability.
        """
        if locker is None:
            locker = acquire_node_dir_lock
        node_dir = self._app.app_node_.node_.node_dir_
        try:
            lock_path = locker(node_dir)
            self._lock_path = str(lock_path)
        except LockError as exc:
            self._app.result_.set_status(Result.Status.LOCKED)
            self._app.app_trace_.logger_.error(str(exc), exc_info=True)
            raise

    def unlock(self) -> None:
        """Release the node lock stored in lock_path.

        No-op when lock_path is not set (lock was never acquired).
        """
        if not self._lock_path:
            return
        release_node_dir_lock(Path.new(self._lock_path))
