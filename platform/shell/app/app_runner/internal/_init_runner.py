"""_init_runner.py
Initialise the appropriate runner type based on the current mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app_runner.app_runner import AppRunner


def _init_runner(runner: 'AppRunner') -> None:
    if runner.is_agent_:
        runner.agent_.init_agent()
    if runner.is_tasker_:
        runner.tasker_.init_tasker()
    if runner.is_router_:
        runner.router_.init_router()
    if runner.is_tool_:
        runner.tool_.init_tool()
    if runner.is_worker_:
        runner.worker_.init_worker()
