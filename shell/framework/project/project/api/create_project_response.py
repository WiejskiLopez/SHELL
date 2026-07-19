from __future__ import annotations

from pydantic import BaseModel


class CreateProjectResponse(BaseModel):
    id: str
