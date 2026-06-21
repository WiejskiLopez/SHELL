"""SubGraphSpawnRequestedEvent — emitowany przez PlannerResultHandler dla każdego spawn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.graph_execution_id import GraphExecutionId
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class SubGraphSpawnRequestedEvent(DomainEvent):
    query: str
    parent_graph_execution_id: GraphExecutionId
    parent_graph_node_id: GraphNodeExecutionId

    @classmethod
    def now(
        cls,
        query: str,
        parent_graph_execution_id: GraphExecutionId,
        parent_graph_node_id: GraphNodeExecutionId,
        now: datetime | None = None,
    ) -> SubGraphSpawnRequestedEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            query=query,
            parent_graph_execution_id=parent_graph_execution_id,
            parent_graph_node_id=parent_graph_node_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            query=payload["query"],
            parent_graph_execution_id=GraphExecutionId(payload["parent_graph_execution_id"]),
            parent_graph_node_id=GraphNodeExecutionId(payload["parent_graph_node_id"]),
        )
