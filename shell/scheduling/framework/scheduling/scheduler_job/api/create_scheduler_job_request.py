from __future__ import annotations

from pydantic import BaseModel


class CreateSchedulerJobRequest(BaseModel):
    scheduler_definition_id: str
    name: str
    job_type: str = "messaging"
    interval_seconds: float = 1.0
    batch_size: int = 50
    enabled: bool = True
