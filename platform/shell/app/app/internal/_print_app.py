"""_print_app.py
Responsible for one thing: printing stdout, stderr and result summary to the output callable.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _print_app(app: 'App', out: Callable[[str], None]) -> None:
    """Print stdout, stderr and result summary from result_ using the given output callable."""
    result = app.result_

    stdout = result.stdout_ or ''
    if stdout:
        out(stdout)

    stderr = result.stderr_ or ''
    if stderr:
        out(stderr)

    not_save_lines = app.app_trace_.not_save_lines_
    if not_save_lines:
        out(not_save_lines)
