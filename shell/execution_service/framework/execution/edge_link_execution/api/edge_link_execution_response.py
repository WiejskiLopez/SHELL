from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EdgeLinkExecutionResponse(BaseModel):
    id: str
    node_execution_id: str | None = None
    edge_execution_id: str | None = None
    created_at: datetime | None = None
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
