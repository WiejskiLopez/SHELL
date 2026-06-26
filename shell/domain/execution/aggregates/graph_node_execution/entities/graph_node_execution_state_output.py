from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_state_output_id import (
    GraphNodeExecutionStateOutputId,
)
from shell.domain.execution.value_objects.is_current import IsCurrent
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.platform.base.entity import Entity
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )


class GraphNodeExecutionStateOutput(Entity[GraphNodeExecutionStateOutputId]):
    __slots__ = ("_graph_node_execution_id", "_payload", "_is_current", "_created_at")

    def __init__(
        self,
        id: GraphNodeExecutionStateOutputId,
        graph_node_execution_id: GraphNodeExecutionId,
        payload: StateData = StateData({}),
        is_current: IsCurrent = IsCurrent(True),
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_node_execution_id = graph_node_execution_id
        self._payload = payload
        self._is_current = is_current
        self._created_at = created_at

    @property
    def graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._graph_node_execution_id

    @property
    def payload(self) -> StateData:
        return self._payload

    @property
    def is_current(self) -> IsCurrent:
        return self._is_current

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at
