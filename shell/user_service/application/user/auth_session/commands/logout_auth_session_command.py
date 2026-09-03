from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class LogoutAuthSessionCommand(Command):
    token: str

    def __post_init__(self) -> None:
        if not self.token:
            raise ValueError("token cannot be empty")
