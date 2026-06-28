from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionGetResultQuery:
    graph_node_execution_id: str
    workflow_id: str
