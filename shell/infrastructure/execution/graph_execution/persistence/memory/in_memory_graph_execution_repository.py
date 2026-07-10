from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorach w repozytorium
)
from shell.platform.infrastructure.persistence.in_memory_repository import (
    InMemoryRepository,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.infrastructure.execution.task_execution.persistence.memory.in_memory_task_execution_repository import (
        InMemoryTaskExecutionRepository,
    )


class InMemoryGraphExecutionRepository(
    InMemoryRepository[GraphExecution, GraphExecutionId], GraphExecutionRepository
):
    _task_executions: InMemoryTaskExecutionRepository | None = None

    def link_task_executions(self, repo: InMemoryTaskExecutionRepository) -> None:
        self._task_executions = repo

    def _active(self) -> list[GraphExecution]:
        return [ge for ge in self._store.values() if ge.deleted_at is None]

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> list[GraphExecution]:
        return [ge for ge in self._active() if ge.task_execution_id == task_execution_id]

    async def get_by_parent_id(
        self, parent_graph_execution_id: GraphExecutionId
    ) -> list[GraphExecution]:
        return [
            ge for ge in self._active() if ge.parent_graph_execution_id == parent_graph_execution_id
        ]
