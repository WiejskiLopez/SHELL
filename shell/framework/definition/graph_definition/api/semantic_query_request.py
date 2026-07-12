from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticQueryRequest(BaseModel):
    query: str
    purpose: str | None = None
    limit: int = Field(default=1, ge=1)
    default_graph_definition_id: str | None = None
