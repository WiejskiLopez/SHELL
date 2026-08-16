from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: str
    user_id: str
    status: str
    opened_at: datetime
    closed_at: datetime | None = None
    created_at: datetime
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
