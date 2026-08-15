from __future__ import annotations

from pydantic import BaseModel


class ChangeUserRequest(BaseModel):
    email: str
