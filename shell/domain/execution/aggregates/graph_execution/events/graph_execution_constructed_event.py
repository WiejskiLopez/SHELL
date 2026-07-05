from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphExecutionConstructedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    task_execution_id: TaskExecutionId

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        now: CreatedAt,
    ) -> GraphExecutionConstructedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
        )
