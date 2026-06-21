"""PlannerSpawnsQueuedEvent — emitowany po zakolejkowaniu wszystkich spawnów przez planner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.graph_execution_id import GraphExecutionId
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class PlannerSpawnsQueuedEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    parent_graph_node_id: GraphNodeExecutionId
    spawn_count: int

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        parent_graph_node_id: GraphNodeExecutionId,
        spawn_count: int,
        now: datetime | None = None,
    ) -> PlannerSpawnsQueuedEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            parent_graph_execution_id=parent_graph_execution_id,
            parent_graph_node_id=parent_graph_node_id,
            spawn_count=spawn_count,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            parent_graph_execution_id=GraphExecutionId(payload["parent_graph_execution_id"]),
            parent_graph_node_id=GraphNodeExecutionId(payload["parent_graph_node_id"]),
            spawn_count=payload.get("spawn_count", 0),
        )
