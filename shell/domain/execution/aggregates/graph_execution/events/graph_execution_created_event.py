from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.value_objects.goal import Goal
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class GraphExecutionCreatedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    task_execution_id: TaskExecutionId
    goal: Goal
    depth: GraphDepth
    parent_graph_execution_id: GraphExecutionId | None = None

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        now: CreatedAt,
        goal: Goal,
        depth: GraphDepth,
        parent_graph_execution_id: GraphExecutionId | None = None,
    ) -> GraphExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            goal=goal,
            depth=depth,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        parent_id = payload["parent_graph_execution_id"]
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            parent_graph_execution_id=GraphExecutionId(parent_id) if parent_id else None,
            goal=Goal(payload.get("goal", "")),
            depth=GraphDepth(payload.get("depth", 0)),
        )
