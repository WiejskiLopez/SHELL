from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SchedulerExecutionResponse(BaseModel):
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
