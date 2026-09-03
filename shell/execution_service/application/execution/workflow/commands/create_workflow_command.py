from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class CreateWorkflowCommand(Command):
    session_id: str
    project_id: str

    def __post_init__(self) -> None:
        pass
