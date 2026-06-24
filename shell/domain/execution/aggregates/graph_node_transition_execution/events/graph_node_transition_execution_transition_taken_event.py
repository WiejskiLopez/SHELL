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
class GraphNodeTransitionExecutionTransitionTakenEvent(DomainEvent):
    transition_id: GraphNodeTransitionExecutionId
    source_node_id: GraphNodeExecutionId
    target_node_id: GraphNodeExecutionId

    @classmethod
    def now(
        cls,
        transition_id: GraphNodeTransitionExecutionId,
        source_node_id: GraphNodeExecutionId,
        target_node_id: GraphNodeExecutionId,
        now: datetime,
    ) -> GraphNodeTransitionExecutionTransitionTakenEvent:
        return cls(
            occurred_at=now,
            transition_id=transition_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            transition_id=GraphNodeTransitionExecutionId(payload["transition_id"]),
            source_node_id=GraphNodeExecutionId(payload["source_node_id"]),
            target_node_id=GraphNodeExecutionId(payload["target_node_id"]),
        )
