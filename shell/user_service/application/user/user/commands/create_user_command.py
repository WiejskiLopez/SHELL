from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class CreateUserCommand(Command):
    email: str

    def __post_init__(self) -> None:
        if not self.email:
            raise ValueError("email cannot be empty")
