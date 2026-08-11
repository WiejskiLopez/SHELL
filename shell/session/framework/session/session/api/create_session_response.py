from __future__ import annotations

from pydantic import BaseModel


class CreateSessionResponse(BaseModel):
    id: str
