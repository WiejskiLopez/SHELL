from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    status: str
    created_at: datetime
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
