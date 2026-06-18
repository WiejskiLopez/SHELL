from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.repositories.workflow_repository import WorkflowRepository
from shell.domain.value_objects.ids import WorkflowId

if TYPE_CHECKING:
    from shell.domain.entities.workflow import Workflow


class InMemoryWorkflowRepository(WorkflowRepository):
    def __init__(self) -> None:
        self._store: dict[str, Workflow] = {}
        self._persisted_versions: dict[str, int] = {}

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        return self._store.get(workflow_id.value)

    async def save(self, workflow: Workflow) -> None:
        from shell.domain.exceptions import WorkflowConcurrentlyModified

        existing_version = self._persisted_versions.get(workflow.id.value)
        if existing_version is None:
            workflow.version = max(workflow.version, 0) + 1
            self._store[workflow.id.value] = workflow
            self._persisted_versions[workflow.id.value] = workflow.version
            return

        if existing_version != workflow.version:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        workflow.version = workflow.version + 1
        self._store[workflow.id.value] = workflow
        self._persisted_versions[workflow.id.value] = workflow.version
