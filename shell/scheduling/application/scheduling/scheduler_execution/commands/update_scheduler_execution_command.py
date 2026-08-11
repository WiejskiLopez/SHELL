from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateSchedulerExecutionCommand:
    scheduler_execution_id: str

    def __post_init__(self) -> None:
        if not self.scheduler_execution_id:
            raise ValueError("scheduler_execution_id cannot be empty")
