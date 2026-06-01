from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _init_app_modules(app: App, mode: str | None, locker) -> None:
    if mode in ('agent', 'tasker', 'router', 'tool', 'worker'):
        app.app_trace_.start_trace()
        app.app_node_.init_app_node()
        app.app_node_.lock_.lock_(locker=locker)
    app.runner_.init_runner(mode=mode)
