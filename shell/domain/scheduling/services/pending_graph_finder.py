from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shell.domain.execution.value_objects.graph_execution_status import (
    GraphExecutionStatus,
)
from shell.domain.execution.value_objects.task_execution_status import (
    TaskExecutionStatus,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.graph_execution import (
        GraphExecution,
    )


class GraphExecutionRepository(Protocol):
    async def find_pending(
        self,
        graph_status: GraphExecutionStatus,
        parent_is_null: bool = False,
        parent_status: GraphExecutionStatus | None = None,
        task_status: TaskExecutionStatus | None = None,
        limit: int = 1,
    ) -> list[GraphExecution]: ...


class PendingGraphFinder:
    async def find_next(
        self,
        repository: GraphExecutionRepository | None,
    ) -> GraphExecution | None:
        if repository is None:
            return None

        graphs = await repository.find_pending(
            graph_status=GraphExecutionStatus.PENDING,
            parent_is_null=False,
            parent_status=GraphExecutionStatus.PLANNING,
            task_status=TaskExecutionStatus.IN_PROGRESS,
            limit=1,
        )
        if graphs:
            return graphs[0]

        graphs = await repository.find_pending(
            graph_status=GraphExecutionStatus.PENDING,
            parent_is_null=True,
            task_status=TaskExecutionStatus.IN_PROGRESS,
            limit=1,
        )
        if graphs:
            return graphs[0]

        return None
