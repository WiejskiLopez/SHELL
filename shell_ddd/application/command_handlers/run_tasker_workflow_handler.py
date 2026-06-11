"""RunTaskerWorkflowHandler — bootstraps a Workflow and emits the first step.

Lifecycle (command side):

1. Validate the task exists and its Graph has nodes.
2. Compute the *first* node via the configured ``NodeNavigator``.
3. Create a ``Workflow`` and call ``Workflow.start_at(first, context, now)``
   which emits ``WorkflowStarted`` + ``NodeStarted``.
4. Persist the workflow (CAS bumps version 0→1) and stage:
   - the workflow's own events (``pull_events``)
   - a kickoff ``NodeExecutionRequested(workflow_id, first_node.id)``
5. Commit and publish.

The actual subprocess orchestration is performed by ``NodeExecutionWorker``
which subscribes to ``NodeExecutionRequested`` (Process Manager / Saga).
This keeps the command handler fast and free of long-running side effects.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import NodeExecutionRequested
from shell_ddd.domain.exceptions import TaskNotFound, WorkflowHasNoNodes
from shell_ddd.domain.services.node_navigator import LinearNodeNavigator
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
        UnitOfWork,
    )
    from shell_ddd.domain.services.node_navigator import NodeNavigator


class RunTaskerWorkflowHandler:
    """Creates a Workflow in RUNNING state and emits the first NodeExecutionRequested.

    Throws ``TaskNotFound`` if the task does not exist and
    ``WorkflowHasNoNodes`` if its Graph has no executable nodes.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        event_publisher: EventPublisher,
        navigator: "NodeNavigator | None" = None,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._event_publisher = event_publisher
        self._navigator: NodeNavigator = navigator or LinearNodeNavigator()

    async def handle(self, cmd: RunTaskerWorkflowCommand) -> str:
        """Persist a RUNNING workflow and request execution; return the workflow id."""
        task_name = TaskName(cmd.task_name)
        now = self._clock.now()

        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(task_name)
            if task is None:
                raise TaskNotFound(cmd.task_name)

            graph = await uow.graphs.get_by_task_id(task.id)
            first_node = self._navigator.first(graph) if graph is not None else None
            if first_node is None:
                raise WorkflowHasNoNodes(cmd.task_name)

            context = WorkflowExecutionContext(
                work_dir=cmd.work_dir,
                correlation_id=str(uuid.uuid4()),
            )

            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_name=cmd.task_name,
                now=now,
            )
            workflow.start_at(
                first_node_id=first_node.id,
                context=context,
                now=now,
            )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
            uow.stage_events(
                [NodeExecutionRequested.now(workflow.id, first_node.id, now=now)]
            )
            await uow.commit()

        await self._event_publisher.publish(uow.events)
        return workflow.id.value
