from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.graph_execution_id import GraphExecutionId
from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionCreatedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    task_execution_id: TaskExecutionId
    parent_graph_execution_id: GraphExecutionId | None = None
    goal: str = ""
    depth: int = 0

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        now: datetime,
        parent_graph_execution_id: GraphExecutionId | None = None,
        goal: str = "",
        depth: int = 0,
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
        parent_id = payload.get("parent_graph_execution_id")
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            parent_graph_execution_id=GraphExecutionId(parent_id) if parent_id else None,
            goal=payload.get("goal", ""),
            depth=payload.get("depth", 0),
        )
