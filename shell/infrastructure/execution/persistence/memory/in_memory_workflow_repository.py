from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.workflow_repository import WorkflowRepository
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow


class InMemoryWorkflowRepository(WorkflowRepository):
    def __init__(self) -> None:
        self._store: dict[str, Workflow] = {}
        self._persisted_versions: dict[str, int] = {}

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        return self._store.get(workflow_id.value)

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> Workflow | None:
        return None

    async def save(self, workflow: Workflow) -> None:
        from shell.domain.execution.exceptions import WorkflowConcurrentlyModified

        existing_version = self._persisted_versions.get(workflow.id.value)
        if existing_version is None:
            new_version = max(workflow.version, 0) + 1
            workflow.apply_new_version(new_version)
            self._store[workflow.id.value] = workflow
            self._persisted_versions[workflow.id.value] = new_version
            return

        if existing_version != workflow.version:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        new_version = workflow.version + 1
        workflow.apply_new_version(new_version)
        self._store[workflow.id.value] = workflow
        self._persisted_versions[workflow.id.value] = new_version
