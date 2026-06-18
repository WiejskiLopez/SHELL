from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.dto.graph_node_execution import GraphNodeExecutionDto


@dataclass(frozen=True, slots=True)
class TaskExecutionDto:
    id: str
    name: str
    version: int
    hash: str
    is_current: bool
    created_at: datetime
    body: str
    graph_node_executions: list[GraphNodeExecutionDto] = field(default_factory=list)
