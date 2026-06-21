from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId
from shell.domain.execution.aggregates.graph_node_execution.value_objects.ids.graph_node_execution_state_input_id import (
    GraphNodeExecutionStateInputId,
)
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime


class GraphNodeExecutionStateInput(Entity[GraphNodeExecutionStateInputId]):
    """Input state for a GraphNodeExecution — child entity."""

    __slots__ = (
        "_graph_node_execution_id",
        "_payload",
        "_is_current",
        "_created_at",
    )

    _graph_node_execution_id: GraphNodeExecutionId
    _payload: dict
    _is_current: bool
    _created_at: datetime

    def __init__(
        self,
        id: GraphNodeExecutionStateInputId,
        graph_node_execution_id: GraphNodeExecutionId,
        payload: dict,
        is_current: bool,
        created_at: datetime,
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
    def payload(self) -> dict:
        return self._payload

    @property
    def is_current(self) -> bool:
        return self._is_current

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @classmethod
    def create(
        cls,
        *,
        id_: GraphNodeExecutionStateInputId,
        graph_node_execution_id: GraphNodeExecutionId,
        payload: dict,
        now: datetime,
    ) -> GraphNodeExecutionStateInput:
        return cls(
            id=id_,
            graph_node_execution_id=graph_node_execution_id,
            payload=payload,
            is_current=True,
            created_at=now,
        )

    def supersede(self) -> None:
        self._is_current = False
