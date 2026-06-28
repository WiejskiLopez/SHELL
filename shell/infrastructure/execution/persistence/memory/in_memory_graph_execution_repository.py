from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorach w repozytorium
)
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.infrastructure.platform.persistence.in_memory_repository import (
    InMemoryRepository,
)

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId
    from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_repository import (
        InMemoryTaskExecutionRepository,
    )


class InMemoryGraphExecutionRepository(InMemoryRepository[GraphExecution, GraphExecutionId], GraphExecutionRepository):
    _task_executions: InMemoryTaskExecutionRepository | None = None

    def link_task_executions(self, repo: InMemoryTaskExecutionRepository) -> None:
        self._task_executions = repo

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> GraphExecution | None:
        for graph_execution in self._store.values():
            if graph_execution.task_execution_id == task_execution_id:
                return graph_execution
        return None

    async def get_by_parent_id(
        self, parent_graph_execution_id: GraphExecutionId
    ) -> list[GraphExecution]:
        return [
            ge
            for ge in self._store.values()
            if ge.parent_graph_execution_id == parent_graph_execution_id
        ]

    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[GraphExecution]:
        if self._task_executions is None:
            return []
        task_ids = [
            te.id.value
            for te in self._task_executions._store.values()
            if te.workflow_id == workflow_id
        ]
        return [ge for ge in self._store.values() if ge.task_execution_id.value in task_ids]
