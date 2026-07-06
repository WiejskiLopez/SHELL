from __future__ import annotations

from pydantic import BaseModel


class EdgeExecutionResponse(BaseModel):
    id: str
