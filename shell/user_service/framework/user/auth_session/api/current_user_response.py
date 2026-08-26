from __future__ import annotations

from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    user_id: str
