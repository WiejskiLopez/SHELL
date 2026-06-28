from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (
    TaskExecutionId,  # noqa: TC002 — TaskExecutionId używany w konstruktorach w repozytorium
)
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.infrastructure.platform.persistence.in_memory_repository import (
    InMemoryRepository,
)

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.ids import WorkflowId
    from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName


class InMemoryTaskExecutionRepository(InMemoryRepository[TaskExecution, TaskExecutionId], TaskExecutionRepository):

    async def get_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        name_value = name.value if hasattr(name, 'value') else str(name)
        for task_execution in self._store.values():
            stored_name = task_execution.name.value if hasattr(task_execution.name, 'value') else str(task_execution.name)
            if stored_name == name_value:
                return task_execution
        return None

    async def get_current_by_id(self, id: TaskExecutionId) -> TaskExecution | None:
        return self._store.get(id.value)

    async def get_current_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        name_value = name.value if hasattr(name, 'value') else str(name)
        for task_execution in self._store.values():
            stored_name = task_execution.name.value if hasattr(task_execution.name, 'value') else str(task_execution.name)
            if stored_name == name_value:
                return task_execution
        return None

    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[TaskExecution]:
        return [te for te in self._store.values() if te.workflow_id == workflow_id]

    async def list_current(self) -> list[TaskExecution]:
        return list(self._store.values())
