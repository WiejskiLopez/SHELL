"""WorkflowRunTaskerHandler — creates a Workflow and starts execution.

Modyfikuje tylko Workflow. TaskExecution workspace i linkage są obsługiwane przez
``WorkflowStartedAttachTaskExecutionHandler`` reagujący na ``WorkflowStartedEvent``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId

if TYPE_CHECKING:
    from shell.application.execution.commands.workflow_commands import RunTaskerWorkflowCommand
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        UnitOfWork,
    )


class WorkflowRunTaskerHandler:
    """Creates a Workflow and emits WorkflowStartedEvent."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, run_tasker_workflow_command: RunTaskerWorkflowCommand) -> str:
        """Persist a RUNNING workflow; return the workflow id."""
        task_execution_id = TaskExecutionId(run_tasker_workflow_command.task_execution_id)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            workflow = Workflow.new(
                id_=self._id_generator.new_id(WorkflowId),
                now=now,
            )
            workflow.start_at(
                now=now,
                task_execution_id=task_execution_id,
                work_dir=run_tasker_workflow_command.work_dir,
            )
            await unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(workflow.pull_events())

        return workflow.id.value
