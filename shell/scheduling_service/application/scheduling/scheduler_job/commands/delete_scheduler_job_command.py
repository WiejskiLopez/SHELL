from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteSchedulerJobCommand:
    scheduler_job_id: str

    def __post_init__(self) -> None:
        if not self.scheduler_job_id:
            raise ValueError("scheduler_job_id cannot be empty")
