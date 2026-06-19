from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    TaskExecutionId
)


@dataclass(frozen=True, slots=True)
class GraphExecutionBuiltEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    task_execution_id: TaskExecutionId
    graph_definition_id: GraphDefinitionId

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionId,
        now: datetime,
    ) -> GraphExecutionBuiltEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            graph_definition_id=GraphDefinitionId(payload["graph_definition_id"]),
        )
