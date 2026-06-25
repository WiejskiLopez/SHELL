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


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionRetriedEvent(DomainEvent):
    node_id: GraphNodeExecutionId
    role: NodeRole
    remaining_retries: int
    retry_delay_seconds: int

    @classmethod
    def now(
        cls,
        node_id: GraphNodeExecutionId,
        role: NodeRole,
        remaining_retries: int,
        retry_delay_seconds: int,
        now: datetime,
    ) -> GraphNodeExecutionRetriedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role,
            remaining_retries=remaining_retries,
            retry_delay_seconds=retry_delay_seconds,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            node_id=GraphNodeExecutionId(payload.get("node_id")),
            role=NodeRole(payload.get("role")),
            remaining_retries=payload.get("remaining_retries", 0),
            retry_delay_seconds=payload.get("retry_delay_seconds", 0),
        )
