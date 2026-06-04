"""_run_app.py
Phase — execute the runner, archive, finalize and return the exit code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.app.app.internal._archive_app import _archive_app
from shell.app.app.internal._finalize_app import _finalize_app
from shell.app.app.internal._result_app import _result_app

if TYPE_CHECKING:
    from shell.app.app.app import App

def _run_app(app: 'App') -> int:
    try:
        app.runner_.run_runner()
        app.app_trace_.stop_trace()
        _archive_app(app)
    finally:
        _finalize_app(app)
    return _result_app(app)