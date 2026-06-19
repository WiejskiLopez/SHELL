from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.repositories.graph_execution_repository import GraphExecutionRepository
from shell.domain.value_objects.ids import GraphExecutionId

if TYPE_CHECKING:
    from shell.domain.aggregates.graph_execution import GraphExecution
    from shell.domain.value_objects.ids import TaskExecutionId


class InMemoryGraphExecutionRepository(GraphExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphExecution] = {}

    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None:
        return self._store.get(graph_execution_id.value)

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> GraphExecution | None:
        for graph_execution in self._store.values():
            if graph_execution.task_execution_id == task_execution_id:
                return graph_execution
        return None

    async def save(self, graph_execution: GraphExecution) -> None:
        self._store[graph_execution.id.value] = graph_execution
