from __future__ import annotations

from pydantic import BaseModel


class NodeDefinitionResponse(BaseModel):
    id: str
    node_type: str
    max_step: int | None = None


class GraphDefinitionResponse(BaseModel):
    id: str
    node_definitions: list[NodeDefinitionResponse]
