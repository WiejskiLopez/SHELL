from shell.utils.path.path import PathType
"""acquire_lock.py
Responsible for one thing: atomically acquiring an exclusive file lock
on a node directory.  Raises LockError when the node is already locked.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from datetime import datetime, timezone

from shell.component.locker.internal._is_stale import _is_stale
from shell.component.locker.internal._lock_error import LockError

LOCK_FILE = "agent.lock"
_STALE_RETRY_DELAY = 0.05


def acquire_node_dir_lock(
    node: PathType,
    clock: Callable[[], datetime] | None = None,
    get_pid: Callable[[], int] | None = None,
    sleep: Callable[[float], None] | None = None,
    create_file: Callable[[PathType, dict], None] | None = None,
    remove_file: Callable[[PathType], None] | None = None,
) -> PathType:
    """Create an atomic lock file and return its path.

    Detects and clears stale locks (process no longer exists).
    Raises LockError if the node is actively locked.
    clock:       optional callable () -> datetime (defaults to datetime.now(utc)).
    get_pid:     optional callable () -> int (defaults to os.getpid).
    sleep:       optional callable (seconds: float) -> None (defaults to time.sleep).
    create_file: optional callable (path: PathType, payload: dict) -> None, must raise
                 FileExistsError when the file already exists (defaults to atomic os.open).
    remove_file: optional callable (path: PathType) -> None (defaults to Path.unlink).
    """
    if clock is None:
        clock = lambda: datetime.now(timezone.utc)
    if get_pid is None:
        get_pid = os.getpid
    if sleep is None:
        sleep = time.sleep
    if create_file is None:
        def create_file(path: PathType, data: dict) -> None:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
    if remove_file is None:
        remove_file = Path.unlink

    lock_path = node / LOCK_FILE
    payload = {
        "pid": get_pid(),
        "timestamp": clock().isoformat(),
    }

    for _ in range(2):
        try:
            create_file(lock_path, payload)
            return lock_path
        except FileExistsError:
            if _is_stale(lock_path):
                try:
                    remove_file(lock_path)
                except FileNotFoundError:
                    pass
                sleep(_STALE_RETRY_DELAY)
                continue
            raise LockError(f"Node is locked by another process: {node}")

    raise LockError(f"Node is locked: {node}")
