from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.process.process.process import Process


def _init_process_agent(process: 'Process', prompt: str, timeout: int, which=None, os_name=None) -> None:
    process.process_command_.init_process_command_agent(process.app_, prompt, timeout, which, os_name)
