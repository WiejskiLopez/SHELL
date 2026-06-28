from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
    GraphNodeExecutionStateId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionStateChangedEvent(DomainEvent):
    graph_node_execution_id: GraphNodeExecutionId
    graph_node_execution_state_id: GraphNodeExecutionStateId
    direction: StateDirection
    key: str
    old_value: object | None = None
    new_value: object | None = None

    @classmethod
    def now(
        cls,
        graph_node_execution_id: GraphNodeExecutionId,
        graph_node_execution_state_id: GraphNodeExecutionStateId,
        direction: StateDirection,
        key: str,
        now: datetime,
        old_value: object | None = None,
        new_value: object | None = None,
    ) -> GraphNodeExecutionStateChangedEvent:
        return cls(
            occurred_at=now,
            graph_node_execution_id=graph_node_execution_id,
            graph_node_execution_state_id=graph_node_execution_state_id,
            direction=direction,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_execution_id=GraphNodeExecutionId(payload.get("graph_node_execution_id")),
            graph_node_execution_state_id=GraphNodeExecutionStateId(payload.get("graph_node_execution_state_id")),
            direction=StateDirection(payload.get("direction")),
            key=payload.get("key"),
            old_value=payload.get("old_value"),
            new_value=payload.get("new_value"),
        )
