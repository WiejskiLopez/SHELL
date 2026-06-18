from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import (
        GraphNodeExecutionId,
        GraphNodeExecutionStateId,
    )


@dataclass(slots=True)
class GraphNodeExecutionState:
    id: GraphNodeExecutionStateId
    graph_node_execution_id: GraphNodeExecutionId
    status: Status
    updated_at: datetime
    step: int = 0
