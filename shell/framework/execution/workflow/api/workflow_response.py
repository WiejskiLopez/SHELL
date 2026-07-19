from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WorkflowResponse(BaseModel):
    id: str
    status: str
    session_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
