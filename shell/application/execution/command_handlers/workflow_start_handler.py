"""StartWorkflowHandler — creates a new Workflow for a task_execution.

Loads the task, transitions the Workflow to ``running`` via ``Workflow.start_at``, and
persists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.exceptions import TaskExecutionNotFound
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId

if TYPE_CHECKING:
    from shell.application.execution.commands.workflow_commands import StartWorkflowCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class WorkflowStartHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, start_workflow_command: StartWorkflowCommand) -> str:
        now = self._clock.now()
        async with self._unit_of_work as unit_of_work:
            task_execution = await unit_of_work.repository(
                TaskExecutionRepository
            ).get_current_by_id(TaskExecutionId(start_workflow_command.task_execution_id))
            if task_execution is None:
                raise TaskExecutionNotFound(start_workflow_command.task_execution_id)

            workflow = Workflow.new(
                id_=self._id_generator.new_id(WorkflowId),
                now=now,
            )
            task_execution.execute_in_workflow(workflow.id)
            await unit_of_work.repository(TaskExecutionRepository).save(task_execution)

            workflow.start_at(
                now=now,
                task_execution_id=task_execution.id,
            )
            await unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(workflow.pull_events())
        return workflow.id.value
