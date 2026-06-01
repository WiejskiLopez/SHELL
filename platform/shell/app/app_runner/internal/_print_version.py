"""_print_version.py
Print agent version and write result to app.result_.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _print_version(runner: 'AppRunner', timer=None) -> None:
    if timer is None:
        timer = time.monotonic
    timer()
    try:
        manifest = runner._app.manifest_
        output = f"{manifest._manifest_name_} {manifest._manifest_version_}"
        runner._app.app_trace_.record_info('runner._print_version._print_version', output)
        runner._app.app_trace_.record_info('runner._print_version._print_version', 'OK')
    except Exception as exc:
        runner._app.app_trace_.record_error_and_raise('runner._print_version._print_version', exc)
