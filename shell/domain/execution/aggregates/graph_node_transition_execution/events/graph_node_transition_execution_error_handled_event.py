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
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class GraphNodeTransitionExecutionErrorHandledEvent(DomainEvent):
    transition_id: GraphNodeTransitionExecutionId
    failed_node_id: GraphNodeExecutionId
    handler_node_id: GraphNodeExecutionId

    @classmethod
    def now(
        cls,
        transition_id: GraphNodeTransitionExecutionId,
        failed_node_id: GraphNodeExecutionId,
        handler_node_id: GraphNodeExecutionId,
        now: CreatedAt,
    ) -> GraphNodeTransitionExecutionErrorHandledEvent:
        return cls(
            occurred_at=now,
            transition_id=transition_id,
            failed_node_id=failed_node_id,
            handler_node_id=handler_node_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            transition_id=GraphNodeTransitionExecutionId(payload["transition_id"]),
            failed_node_id=GraphNodeExecutionId(payload["failed_node_id"]),
            handler_node_id=GraphNodeExecutionId(payload["handler_node_id"]),
        )
