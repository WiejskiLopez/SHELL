from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.ports.task_execution_repository import TaskExecutionRepository
from shell.domain.execution.value_objects.ids import (
    TaskExecutionId,  # noqa: TC002 — TaskExecutionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
    from shell.domain.execution.value_objects.ids import WorkflowId
    from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName


class InMemoryTaskExecutionRepository(TaskExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecution] = {}

    async def get_by_id(self, task_execution_id: TaskExecutionId) -> TaskExecution | None:
        return self._store.get(task_execution_id.value)

    async def get_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        for task_execution in self._store.values():
            if task_execution.name == name:
                return task_execution
        return None

    async def get_current_by_id(self, id: TaskExecutionId) -> TaskExecution | None:
        task_execution = self._store.get(id.value)
        if task_execution and task_execution.is_current:
            return task_execution
        return None

    async def get_current_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        for task_execution in self._store.values():
            if task_execution.name == name and task_execution.is_current:
                return task_execution
        return None

    async def save(self, task_execution: TaskExecution) -> None:
        self._store[task_execution.id.value] = task_execution

    async def get_by_workflow_id(
        self, workflow_id: WorkflowId
    ) -> list[TaskExecution]:
        return [
            te for te in self._store.values()
            if te.workflow_id == workflow_id
        ]

    async def list_current(self) -> list[TaskExecution]:
        return [task_execution for task_execution in self._store.values() if task_execution.is_current]
