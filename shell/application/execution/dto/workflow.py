from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.execution.dto.graph_node_execution_state import (
        GraphNodeExecutionStateDto,
    )


@dataclass(frozen=True, slots=True)
class WorkflowDto:
    id: str
    status: str
    created_at: datetime
    version: int = 0
    cursor: str | None = None
    graph_node_execution_states: dict[str, GraphNodeExecutionStateDto] = field(default_factory=dict)
