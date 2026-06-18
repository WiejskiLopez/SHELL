from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphExecutionDto:
    id: str
    graph_definition_id: str
    task_execution_id: str
