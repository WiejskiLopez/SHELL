from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateSchedulerJobCommand:
    scheduler_definition_id: str
    name: str
    job_type: str = "messaging"
    interval_seconds: float = 1.0
    batch_size: int = 50
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.scheduler_definition_id:
            raise ValueError("scheduler_definition_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
