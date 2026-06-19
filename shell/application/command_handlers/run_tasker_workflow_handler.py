"""RunTaskerWorkflowHandler — bootstraps a Workflow and emits the first step.

Lifecycle (command side):

1. Validate the task exists and its Graph has nodes.
2. Compute the *first* node via the configured ``NodeNavigator``.
3. Create a ``Workflow`` and call ``Workflow.start_at(first, context, now)``
   which emits ``WorkflowStartedEvent`` + ``GraphNodeExecutionStartedEvent``.
4. Persist the workflow (CAS bumps version 0→1) and stage:
   - the workflow's own events (``pull_events``)
   - a kickoff ``GraphNodeExecutionRequestedEvent(workflow_id, first_graph_node_execution.id)``
5. Commit and publish.

The actual subprocess orchestration is performed by ``GraphNodeExecutionWorker``
which subscribes to ``GraphNodeExecutionRequestedEvent`` (Process Manager / Saga).
This keeps the command handler fast and free of long-running side effects.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell.domain.aggregates.workflow import Workflow
from shell.domain.events.events import GraphNodeExecutionRequestedEvent
from shell.domain.exceptions import TaskExecutionNotFound, WorkflowHasNoNodes
from shell.domain.services.graph_node_execution_navigator import LinearGraphNodeExecutionNavigator
from shell.domain.value_objects.ids import TaskExecutionId
from shell.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

if TYPE_CHECKING:
    from shell.application.commands.commands import RunTaskerWorkflowCommand
    from shell.application.ports.ports import (
        Clock,
        IdGenerator,
        UnitOfWork,
    )
    from shell.domain.services.graph_node_execution_navigator import NodeNavigator


class RunTaskerWorkflowHandler:
    """Creates a Workflow in RUNNING state and emits the first GraphNodeExecutionRequestedEvent.

    Throws ``TaskExecutionNotFound`` if the task does not exist and
    ``WorkflowHasNoNodes`` if its GraphExecution has no executable nodes.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        navigator: NodeNavigator | None = None,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._navigator: NodeNavigator = navigator or LinearGraphNodeExecutionNavigator()

    async def handle(self, cmd: RunTaskerWorkflowCommand) -> str:
        """Persist a RUNNING workflow and request execution; return the workflow id."""
        task_execution_id = TaskExecutionId(cmd.task_execution_id)
        now = self._clock.now()

        async with self._uow as uow:
            task_execution = await uow.task_executions.get_current_by_id(task_execution_id)
            if task_execution is None:
                raise TaskExecutionNotFound(cmd.task_execution_id)

            graph_execution = await uow.graph_executions.get_by_task_execution_id(task_execution.id)
            first_graph_node_execution = (
                self._navigator.first(graph_execution) if graph_execution is not None else None
            )
            if first_graph_node_execution is None:
                raise WorkflowHasNoNodes(cmd.task_execution_id)

            context = WorkflowExecutionContext(
                correlation_id=str(uuid.uuid4()),
            )

            task_execution.work_dir = cmd.work_dir
            await uow.task_executions.save(task_execution)

            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_execution_id=task_execution_id,
                now=now,
            )
            workflow.start_at(
                first_graph_node_execution_id=first_graph_node_execution.id,
                context=context,
                now=now,
            )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
            uow.stage_events(
                [
                    GraphNodeExecutionRequestedEvent.now(
                        workflow.id, first_graph_node_execution.id, now=now
                    )
                ]
            )

        return workflow.id.value
