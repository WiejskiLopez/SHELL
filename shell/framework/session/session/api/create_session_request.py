from __future__ import annotations

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=1000)
