from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SchedulerJobDto:
    id: str
    scheduler_definition_id: str
    status: str
    created_at: datetime
    trigger_event_id: str | None = None
    trigger_event_type: str | None = None
    action_ref: str | None = None
    action_ref_type: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None
