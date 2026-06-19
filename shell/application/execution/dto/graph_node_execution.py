from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionDto:
    id: str
    position: int
    mode: str
    role: str
    node_type: str
    model: str
    command: str
    sub_graph_definition_id: str | None = None
    sub_graph_definition_version: int | None = None
