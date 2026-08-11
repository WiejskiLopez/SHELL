from __future__ import annotations

from pydantic import BaseModel


class UpdateUserRequest(BaseModel):
    email: str
