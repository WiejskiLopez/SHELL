from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class SchedulerExecutionDto:
    id: str
    scheduler_definition_id: str
    created_at: datetime
    name: str = ""
    job_type: str = "messaging"
    interval_seconds: float = 1.0
    batch_size: int = 50
    enabled: bool = True
    config: JsonStr | None = None
    updated_at: datetime | None = None
