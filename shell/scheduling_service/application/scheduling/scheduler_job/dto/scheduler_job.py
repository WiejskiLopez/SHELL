from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class SchedulerJobDto:
    id: str
    scheduler_definition_id: str
    name: str
    created_at: datetime
    job_type: str = "messaging"
    interval_seconds: float = 1.0
    batch_size: int = 50
    enabled: bool = True
    config: JsonStr | None = None
    changed_at: datetime | None = None
