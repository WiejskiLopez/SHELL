"""command.py
Command — value object wrapping a CLI command as a list of string arguments.

Slots:
    _command — list[str]; the assembled CLI arguments
"""

from __future__ import annotations


class Command:
    """Value object wrapping a CLI command argument list."""

    __slots__ = ("_command",)

    def __init__(self, command: list[str]) -> None:
        self._command = command

    @property
    def command_(self) -> list[str]:
        return self._command

    def add_command_arg(self, arg: str) -> None:
        self._command.append(arg)

    def extend_command_args(self, args: list[str]) -> None:
        self._command.extend(args)
