from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from datetime import datetime


@dataclass(frozen=True, slots=True)
class GraphExecutionDto:
    id: str
    graph_definition_id: str
    task_execution_id: str
    parent_graph_execution_id: str | None = None
    parent_tasker_node_execution_id: str | None = None
    state_input: dict[str, Any] | None = None
    state_output: dict[str, Any] | None = None
    depth: int = 0
    timeout_at: datetime | None = None
    correlation_id: str = ""
    tags: dict[str, Any] | None = None
