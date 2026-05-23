"""_result_app.py
Phase — resolve final status and return the OS exit code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.result.result import Result
from shell.app.app.internal._print_app import _print_app

if TYPE_CHECKING:
    from shell.app.app.app import App


def _result_app(app: 'App', out=None) -> int:
    if out is None:
        out = print
    app.app_trace_.record_summary()
    _print_app(app, out)
    return app.result_.returncode_
