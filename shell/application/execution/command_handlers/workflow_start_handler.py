"""WorkflowStartHandler — creates a new Workflow for a task_execution.

Modyfikuje tylko Workflow. TaskExecution jest aktualizowany przez
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
            workflow = Workflow.new(
                id_=self._id_generator.new_id(WorkflowId),
                now=now,
            )
            workflow.start_at(
                now=now,
                task_execution_id=TaskExecutionId(start_workflow_command.task_execution_id),
            )
            await unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(workflow.pull_events())
        return workflow.id.value
