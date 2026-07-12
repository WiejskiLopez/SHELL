from __future__ import annotations

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
