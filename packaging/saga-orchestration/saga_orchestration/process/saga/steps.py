from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import timedelta


@dataclass(frozen=True, slots=True)
class StepDefinition:
    name: str
    target_service: str
    compensation_command: type[object] | None = None
    compensate_on_failure: bool = False
    awaited_by: type[object] | None = None
    timeout: timedelta | None = None


@dataclass(frozen=True, slots=True)
class StepRegistry:
    steps: tuple[StepDefinition, ...]

    def by_name(self, name: str) -> StepDefinition:
        for step in self.steps:
            if step.name == name:
                return step
        raise KeyError(f"No such step: {name}")
