from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class ChangeSchedulerDefinitionCommand(Command):
    scheduler_definition_id: str

    def __post_init__(self) -> None:
        if not self.scheduler_definition_id:
            raise ValueError("scheduler_definition_id cannot be empty")
