from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class SchedulerExecutionDto:
    id: str
    scheduler_definition_id: str
    name: str = ""
    job_type: str = "messaging"
    interval_seconds: float = 1.0
    batch_size: int = 50
    enabled: bool = True
    config: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
