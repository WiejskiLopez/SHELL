from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSchedulerJobByIdQuery:
    scheduler_job_id: str
