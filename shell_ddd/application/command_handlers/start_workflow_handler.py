"""StartWorkflowHandler — creates a new Workflow for a task."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import WorkflowStarted
from shell_ddd.domain.exceptions import TaskNotFound
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import StartWorkflowCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, IdGenerator, UnitOfWork


class StartWorkflowHandler:
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

    async def handle(self, cmd: StartWorkflowCommand) -> str:
        current_time = self._clock.now()
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(TaskName(cmd.task_name))
            if task is None:
                raise TaskNotFound(cmd.task_name)
            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_name=cmd.task_name,
                now=current_time,
            )
            workflow.start(now=current_time)
            await uow.workflows.save(workflow)
            uow.stage_events([WorkflowStarted.now(workflow.id, cmd.task_name, now=current_time)])
            await uow.commit()
        await self._event_publisher.publish(uow.events)
        return workflow.id.value
