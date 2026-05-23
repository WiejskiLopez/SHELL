from __future__ import annotations

from shell.component.process.process_command.process_command import ProcessCommand


def _init_process_command(process: 'Process') -> None:
    process._process_command = ProcessCommand()
