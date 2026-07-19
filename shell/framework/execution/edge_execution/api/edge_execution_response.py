from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EdgeExecutionResponse(BaseModel):
    id: str
    edge_definition_id: str | None = None
    source_node_execution_id: str | None = None
    target_node_execution_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
