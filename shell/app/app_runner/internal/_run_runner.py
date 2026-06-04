"""_run_runner.py
Dispatch CLI flags to the appropriate runner domain method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.app.app_runner.internal._clean_node import _clean_node
from shell.app.app_runner.internal._print_help import _print_help
from shell.app.app_runner.internal._print_version import _print_version

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _run_runner(runner: 'AppRunner', timer=None) -> None:
    try:
        if runner._app.cli_.cli_properties_.is_help_:
            _print_help(runner, timer=timer)
        elif runner._app.cli_.cli_properties_.is_version_:
            _print_version(runner, timer=timer)
        elif runner._app.cli_.cli_properties_.is_clean_:
            _clean_node(runner, timer=timer)
        elif runner.is_agent_:
            runner.agent_.run_agent()
        elif runner.is_tasker_:
            runner.tasker_.run_tasker()
        elif runner.is_router_:
            runner.router_.run_router()
        elif runner.is_tool_:
            runner.tool_.run_tool()
        elif runner.is_worker_:
            runner.worker_.run_worker()
        else:
            raise ValueError("Invalid mode: no valid CLI flags found and no valid mode set.")
        runner._app.app_trace_.record_info('runner._run_runner._run_runner', 'successfully executed')
    except Exception as exc:  # noqa: BLE001
        runner._app.app_trace_.record_error('runner._run_runner._run_runner', exc)
