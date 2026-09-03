from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class DeleteEdgeLinkExecutionCommand(Command):
    id: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id cannot be empty")
