from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.application.execution.workflow.commands.update_workflow_command import (
        UpdateWorkflowCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class WorkflowNotFoundError(Exception):
    pass


class UpdateWorkflowHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: UpdateWorkflowCommand) -> None:
        workflow_id = WorkflowId(command.workflow_id)

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFoundError(f"Workflow '{command.workflow_id}' not found")

            now = UpdatedAt.from_datetime(self._clock.now())
            workflow.update(now)
            await unit_of_work.save(WorkflowRepository, workflow)
