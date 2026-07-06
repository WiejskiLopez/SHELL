from __future__ import annotations

from pydantic import BaseModel


class EdgeLinkExecutionResponse(BaseModel):
    id: str
