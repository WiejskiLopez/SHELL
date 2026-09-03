"""Tabela kroków sagi — definicje kroków i kompensacje."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import timedelta

    from shell.platform.application.commands.command import Command
    from shell.platform.application.events.integration_event import IntegrationEvent


@dataclass(frozen=True, slots=True)
class StepDefinition:
    """Opis jednego kroku procesu: gdzie leci, kiedy timeout, jak cofnąć."""

    name: str
    target_service: str
    compensation_command: type[Command] | None = None
    compensate_on_failure: bool = False
    awaited_by: type[IntegrationEvent] | None = None
    timeout: timedelta | None = None


@dataclass(frozen=True, slots=True)
class StepRegistry:
    """Fail-fast indeks kroków po nazwie."""

    steps: tuple[StepDefinition, ...]

    def by_name(self, name: str) -> StepDefinition:
        for step in self.steps:
            if step.name == name:
                return step
        raise KeyError(f"No such step: {name}")
