from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: str
    goal: str
    status: str
    opened_at: datetime
    closed_at: datetime | None = None
