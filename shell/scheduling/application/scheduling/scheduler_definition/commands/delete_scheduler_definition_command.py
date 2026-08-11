from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteSchedulerDefinitionCommand:
    scheduler_definition_id: str

    def __post_init__(self) -> None:
        if not self.scheduler_definition_id:
            raise ValueError("scheduler_definition_id cannot be empty")
