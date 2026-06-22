"""StartWorkflowHandler — creates a new Workflow for a task_execution.

Loads the task, transitions the Workflow to ``running`` via ``Workflow.start_at``, and
persists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.exceptions import TaskExecutionNotFound
from shell.domain.execution.value_objects.ids import TaskExecutionId

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import StartWorkflowCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class StartWorkflowHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: StartWorkflowCommand) -> str:
        now = self._clock.now()
        async with self._uow as uow:
            task_execution = await uow.task_executions.get_current_by_id(
                TaskExecutionId(cmd.task_execution_id)
            )
            if task_execution is None:
                raise TaskExecutionNotFound(cmd.task_execution_id)

            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                now=now,
            )
            task_execution.execute_in_workflow(workflow.id)
            await uow.task_executions.save(task_execution)

            workflow.start_at(
                now=now,
                task_execution_id=task_execution.id,
            )
            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
        return workflow.id.value
