from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class CreateSchedulerDefinitionCommand(Command):
    name: str
    trigger_config: dict[str, Any]
    action_config: dict[str, Any]
    execution_policy: dict[str, Any]
    enabled: bool = True
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name cannot be empty")
