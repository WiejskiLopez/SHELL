from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SchedulerJobResponse(BaseModel):
    id: str
    scheduler_definition_id: str
    name: str
    job_type: str = "messaging"
    interval_seconds: float = 1.0
    batch_size: int = 50
    enabled: bool = True
    created_at: datetime
    updated_at: datetime | None = None
