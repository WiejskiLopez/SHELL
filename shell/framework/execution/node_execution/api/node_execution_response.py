from __future__ import annotations

from pydantic import BaseModel


class NodeExecutionResponse(BaseModel):
    id: str
    node_type: str | None = None
    status: str | None = None
