"""process_command.py
ProcessCommand: holds the Command for a single subprocess invocation.

Slots:
    _command — Command; the CLI command to execute
"""

from __future__ import annotations

from shell.component.command.command import Command
from shell.component.process.process_command.internal._init_process_command import _init_process_command


class ProcessCommand:
    """Holds the assembled CLI command for a Process."""

    __slots__ = ("_command",)

    def __init__(self) -> None:
        self._command: Command | None = None

    @property
    def command_(self) -> Command:
        return self._command

    def init_process_command(self) -> None:
        _init_process_command(self)
