from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.value_objects.ids import (
        GraphNodeExecutionId,
        GraphNodeExecutionInputPayloadId,
    )


class GraphNodeExecutionInputPayload(AggregateRoot["GraphNodeExecutionInputPayloadId"]):
    """Input payload for a GraphNodeExecution."""

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
        id: GraphNodeExecutionInputPayloadId,
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
        id_: GraphNodeExecutionInputPayloadId,
        graph_node_execution_id: GraphNodeExecutionId,
        payload: dict,
        now: datetime,
    ) -> GraphNodeExecutionInputPayload:
        return cls(
            id=id_,
            graph_node_execution_id=graph_node_execution_id,
            payload=payload,
            is_current=True,
            created_at=now,
        )

    def supersede(self) -> None:
        self._is_current = False
