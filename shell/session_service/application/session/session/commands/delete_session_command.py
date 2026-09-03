from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class DeleteSessionCommand(Command):
    session_id: str

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
