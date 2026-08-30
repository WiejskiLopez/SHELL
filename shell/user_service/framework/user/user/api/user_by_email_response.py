from __future__ import annotations

from pydantic import BaseModel


class UserByEmailResponse(BaseModel):
    id: str
