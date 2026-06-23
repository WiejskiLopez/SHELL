from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.ids.graph_node_execution_state_input_id import (
    GraphNodeExecutionStateInputId,
)
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime


class GraphNodeExecutionStateInput(Entity[GraphNodeExecutionStateInputId]):
    __slots__ = (
        "_graph_node_execution_id",
        "_payload",
        "_created_at",
    )

    _graph_node_execution_id: GraphNodeExecutionId
    _payload: dict[str, Any]
    _created_at: datetime

    def __init__(
        self,
        id: GraphNodeExecutionStateInputId,
        graph_node_execution_id: GraphNodeExecutionId,
        payload: dict[str, Any],
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._graph_node_execution_id = graph_node_execution_id
        self._payload = payload
        self._created_at = created_at

    @property
    def graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._graph_node_execution_id

    @property
    def payload(self) -> dict[str, Any]:
        return self._payload

    @property
    def created_at(self) -> datetime:
        return self._created_at
