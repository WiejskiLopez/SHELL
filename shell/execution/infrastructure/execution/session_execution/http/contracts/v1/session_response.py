from __future__ import annotations

from pydantic import BaseModel


class SessionResponseV1(BaseModel):
    id: str
