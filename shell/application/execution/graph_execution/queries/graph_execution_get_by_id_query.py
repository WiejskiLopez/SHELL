from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphExecutionGetByIdQuery:
    graph_execution_id: str
