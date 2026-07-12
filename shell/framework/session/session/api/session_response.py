from __future__ import annotations

from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: str
    goal: str
    status: str
    opened_at: str | None = None
    closed_at: str | None = None
