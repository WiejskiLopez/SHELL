"""_clean_node.py
Clean node output directories and write result to app.result_.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _clean_node(runner: 'AppRunner', timer=None) -> None:
    """Clean node output directories and write result to app.result_."""
    if timer is None:
        timer = time.monotonic
    timer()
    try:
        runner._app.app_node_.node_.clean_node()
        runner._app.app_trace_.record_info('runner._clean_node._clean_node', 'Node output cleaned.')
    except Exception as exc:
        runner._app.app_trace_.record_error_and_raise('runner._clean_node._clean_node', exc)
