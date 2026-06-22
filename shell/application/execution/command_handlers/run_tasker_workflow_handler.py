"""RunTaskerWorkflowHandler — bootstraps a Workflow and emits the first step.

Lifecycle (command side):

1. Validate the task exists.
2. Create a ``Workflow`` and call ``Workflow.start_at(now)``.
3. Persist the workflow, request first node, and stage events.
4. Commit and publish.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_requested_event import (
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.execution.exceptions import TaskExecutionNotFound
from shell.domain.execution.value_objects.ids import TaskExecutionId

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import RunTaskerWorkflowCommand
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        UnitOfWork,
    )


class RunTaskerWorkflowHandler:
    """Creates a Workflow in RUNNING state and emits the first GraphNodeExecutionRequestedEvent."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: RunTaskerWorkflowCommand) -> str:
        """Persist a RUNNING workflow and request execution; return the workflow id."""
        task_execution_id = TaskExecutionId(cmd.task_execution_id)
        now = self._clock.now()

        async with self._uow as uow:
            task_execution = await uow.task_executions.get_current_by_id(task_execution_id)
            if task_execution is None:
                raise TaskExecutionNotFound(cmd.task_execution_id)

            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                now=now,
            )
            task_execution.prepare_workspace(cmd.work_dir)
            task_execution.execute_in_workflow(workflow.id)
            await uow.task_executions.save(task_execution)

            workflow.start_at(
                now=now,
                task_execution_id=task_execution_id,
            )

            graph_executions = await uow.graph_executions.get_by_workflow_id(workflow.id)
            if graph_executions:
                first_node_ids = graph_executions[0].graph_node_execution_ids
                if first_node_ids:
                    uow.stage_events([
                        GraphNodeExecutionRequestedEvent.now(
                            workflow_id=workflow.id,
                            graph_node_execution_id=first_node_ids[0],
                            now=now,
                        ),
                    ])

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())

        return workflow.id.value
