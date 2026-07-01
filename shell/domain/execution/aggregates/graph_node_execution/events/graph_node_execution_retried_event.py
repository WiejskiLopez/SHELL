from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionRetriedEvent(DomainEvent):
    node_id: GraphNodeExecutionId
    role: NodeRole

    @classmethod
    def now(
        cls,
        node_id: GraphNodeExecutionId,
        role: NodeRole,
        now: CreatedAt,
    ) -> GraphNodeExecutionRetriedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            node_id=GraphNodeExecutionId(payload["node_id"]),
            role=NodeRole(payload["role"]),
        )
