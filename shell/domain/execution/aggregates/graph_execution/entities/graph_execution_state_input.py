from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.execution.value_objects.ids import GraphExecutionStateInputId, GraphExecutionId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class GraphExecutionStateInput:
    id: GraphExecutionStateInputId
    graph_execution_id: GraphExecutionId
    payload: dict[str, Any]
    created_at: datetime
