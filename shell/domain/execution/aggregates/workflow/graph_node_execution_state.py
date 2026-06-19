from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base.entity import Entity
from shell.domain.platform.value_objects.ids import GraphNodeExecutionStateId
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.value_objects.ids import GraphNodeExecutionId


class GraphNodeExecutionState(Entity[GraphNodeExecutionStateId]):
    __slots__ = ("graph_node_execution_id", "status", "updated_at", "step")

    def __init__(
        self,
        id: GraphNodeExecutionStateId,
        graph_node_execution_id: GraphNodeExecutionId,
        status: Status,
        updated_at: datetime,
        step: int = 0,
    ) -> None:
        super().__init__(id)
        self.graph_node_execution_id = graph_node_execution_id
        self.status = status
        self.updated_at = updated_at
        self.step = step
