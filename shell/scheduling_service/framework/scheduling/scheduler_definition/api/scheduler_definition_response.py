from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SchedulerDefinitionResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    enabled: bool = True
    created_at: datetime
    changed_at: datetime | None = None
