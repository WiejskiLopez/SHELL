"""GraphExecutionRepository port — persistence boundary for the Graph aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.value_objects.ids import GraphExecutionId, TaskExecutionId


class GraphExecutionRepository(Protocol):
    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None: ...
    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> GraphExecution | None: ...
    async def save(self, graph_execution: GraphExecution) -> None: ...
