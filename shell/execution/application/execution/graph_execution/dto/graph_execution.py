from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
)

from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class GraphExecutionDto:
    id: str
    graph_definition_id: str
    task_execution_id: str
    parent_graph_execution_id: str | None = None
    state_data: JsonStr | None = None
    depth: int = 0
    timeout_at: datetime | None = None
