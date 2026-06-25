from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,
)
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeTransitionExecutionLoopedEvent(DomainEvent):
    transition_id: GraphNodeTransitionExecutionId
    source_node_id: GraphNodeExecutionId
    iteration: int = 0

    @classmethod
    def now(
        cls,
        transition_id: GraphNodeTransitionExecutionId,
        source_node_id: GraphNodeExecutionId,
        now: datetime,
        iteration: int = 0,
    ) -> GraphNodeTransitionExecutionLoopedEvent:
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
            occurred_at=occurred_at,
            schema_version=schema_version,
            transition_id=GraphNodeTransitionExecutionId(payload.get("transition_id")),
            source_node_id=GraphNodeExecutionId(payload.get("source_node_id")),
            iteration=payload.get("iteration", 0),
        )
