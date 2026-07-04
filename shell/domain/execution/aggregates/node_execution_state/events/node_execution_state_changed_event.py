from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
    NodeExecutionStateId,
)
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion
from shell.domain.platform.value_objects.state_direction import StateDirection


@dataclass(frozen=True, slots=True)
class NodeExecutionStateChangedEvent(DomainEvent):
    node_execution_id: NodeExecutionId
    node_execution_state_id: NodeExecutionStateId
    direction: StateDirection
    key: str
    old_value: object | None = None
    new_value: object | None = None

    @classmethod
    def now(
        cls,
        node_execution_id: NodeExecutionId,
        node_execution_state_id: NodeExecutionStateId,
        direction: StateDirection,
        key: str,
        now: CreatedAt,
        old_value: object | None = None,
        new_value: object | None = None,
    ) -> NodeExecutionStateChangedEvent:
        return cls(
            occurred_at=now,
            node_execution_id=node_execution_id,
            node_execution_state_id=node_execution_state_id,
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
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            node_execution_id=NodeExecutionId(payload["node_execution_id"]),
            node_execution_state_id=NodeExecutionStateId(
                payload["node_execution_state_id"]
            ),
            direction=StateDirection(payload["direction"]),
            key=payload["key"],
            old_value=payload["old_value"],
            new_value=payload["new_value"],
        )
