"""RunTaskerWorkflowHandler — creates a RUNNING Workflow and fires WorkflowExecutionRequested.

The actual subprocess orchestration is performed by WorkflowExecutionWorker, which
subscribes to WorkflowExecutionRequested via the EventBus.  This keeps the command
handler fast and non-blocking (Process Manager / Saga pattern).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import WorkflowExecutionRequested, WorkflowStarted
from shell_ddd.domain.exceptions import TaskNotFound
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, IdGenerator, UnitOfWork


class RunTaskerWorkflowHandler:
    """Creates a Workflow in RUNNING state and emits WorkflowExecutionRequested.

    Workflow lifecycle (command side):
    1. Validate the task exists.
    2. Create a new Workflow and mark it ``running``.
    3. Stage WorkflowStarted + WorkflowExecutionRequested and commit.
    4. Publish events (WorkflowExecutionWorker picks up the execution request).
    5. Return the new workflow id immediately — no subprocesses are started here.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._event_publisher = event_publisher

    async def handle(self, cmd: RunTaskerWorkflowCommand) -> str:
        """Persist a RUNNING workflow and request execution; return the workflow id."""
        task_name = TaskName(cmd.task_name)
        now = self._clock.now()

        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(task_name)
            if task is None:
                raise TaskNotFound(cmd.task_name)

            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_name=cmd.task_name,
                now=now,
            )
            workflow.start(now=now)
            await uow.workflows.save(workflow)
            uow.stage_events([
                WorkflowStarted.now(workflow_id=workflow.id, task_name=cmd.task_name, now=now),
                WorkflowExecutionRequested.now(
                    workflow_id=workflow.id,
                    task_name=cmd.task_name,
                    work_dir=cmd.work_dir,
                    max_parallel=cmd.max_parallel,
                    now=now,
                ),
            ])
            await uow.commit()

        await self._event_publisher.publish(uow.events)
        return workflow.id.value
