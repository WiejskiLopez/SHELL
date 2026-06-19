from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> Workflow | None: ...
    async def save(self, workflow: Workflow) -> None: ...
