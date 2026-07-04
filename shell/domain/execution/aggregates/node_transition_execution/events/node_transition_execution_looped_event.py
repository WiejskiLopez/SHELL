from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_transition_execution.value_objects.node_transition_execution_id import (
    NodeTransitionExecutionId,
)
from shell.domain.execution.value_objects.current_iteration import CurrentIteration
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class NodeTransitionExecutionLoopedEvent(DomainEvent):
    transition_id: NodeTransitionExecutionId
    source_node_id: NodeExecutionId
    iteration: CurrentIteration

    @classmethod
    def now(
        cls,
        transition_id: NodeTransitionExecutionId,
        source_node_id: NodeExecutionId,
        now: CreatedAt,
        iteration: CurrentIteration,
    ) -> NodeTransitionExecutionLoopedEvent:
        return cls(
            occurred_at=now,
            transition_id=transition_id,
            source_node_id=source_node_id,
            iteration=iteration,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            transition_id=NodeTransitionExecutionId(payload["transition_id"]),
            source_node_id=NodeExecutionId(payload["source_node_id"]),
            iteration=CurrentIteration(payload.get("iteration", 0)),
        )
