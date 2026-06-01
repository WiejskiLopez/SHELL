from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from shell.utils.path.path import PathType
from shell.component.locker.internal._acquire_node_dir_lock import acquire_node_dir_lock
from shell.component.locker.internal._lock_error import LockError
from shell.component.result.result import Result

if TYPE_CHECKING:
    from shell.component.locker.locker import Locker


def _acquire_locker(locker: 'Locker', acquirer: Callable[[PathType], PathType] | None = None) -> None:
    if acquirer is None:
        acquirer = acquire_node_dir_lock
    app = locker._app
    node_dir = app.app_node_.node_.node_dir_
    app.app_trace_.record_info('locker.acquire.begin', f'node_dir={node_dir}')
    try:
        lock_path = acquirer(node_dir)
        locker._lock_path = str(lock_path)
        app.app_trace_.record_info('locker.acquire.ok', f'lock_path={lock_path}')
    except LockError as exc:
        app.result_.set_status(Result.Status.LOCKED)
        app.app_trace_.record_error('locker.acquire.fail', exc)
        raise
