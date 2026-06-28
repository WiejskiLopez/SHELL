from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.execution.value_objects.state_key import StateKey
from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphExecutionStateChangedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    graph_execution_state_id: GraphExecutionStateId
    direction: StateDirection
    key: StateKey
    old_value: object | None
    new_value: object | None

    @classmethod
    def now(
        cls,
        *,
        graph_execution_id: GraphExecutionId,
        graph_execution_state_id: GraphExecutionStateId,
        direction: StateDirection,
        key: StateKey,
        old_value: object | None,
        new_value: object | None,
        now: datetime,
    ) -> GraphExecutionStateChangedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            graph_execution_state_id=graph_execution_state_id,
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
            graph_execution_id=payload.get("graph_execution_id"),
            graph_execution_state_id=payload.get("graph_execution_state_id"),
            direction=StateDirection(payload.get("direction", "IN")),
            key=StateKey(payload.get("key")),
            old_value=payload.get("old_value"),
            new_value=payload.get("new_value"),
            schema_version=schema_version,
        )
