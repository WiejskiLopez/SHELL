from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionCompletedEvent(DomainEvent):
    node_id: GraphNodeExecutionId
    role: NodeRole
    result: StateData | None = None

    @classmethod
    def now(
        cls,
        node_id: GraphNodeExecutionId,
        role: NodeRole,
        now: datetime,
        result: StateData | None = None,
    ) -> GraphNodeExecutionCompletedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role,
            result=result,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, object], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            node_id=GraphNodeExecutionId(payload.get("node_id")),
            role=NodeRole(payload.get("role")),
            result=StateData(payload["result"]) if "result" in payload and payload["result"] is not None else None,
        )
