from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.goal import Goal
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class GraphExecutionSpawnedEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    child_graph_execution_id: GraphExecutionId
    goal: Goal

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
        now: CreatedAt,
        goal: Goal,
    ) -> GraphExecutionSpawnedEvent:
        return cls(
            occurred_at=now,
            parent_graph_execution_id=parent_graph_execution_id,
            child_graph_execution_id=child_graph_execution_id,
            goal=goal,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            parent_graph_execution_id=GraphExecutionId(payload["parent_graph_execution_id"]),
            child_graph_execution_id=GraphExecutionId(payload["child_graph_execution_id"]),
            goal=Goal(payload.get("goal", "")),
        )
