"""WorkflowRunTaskerHandler — bootstraps a Workflow and emits the first step.

Lifecycle (command side):

1. Validate the task exists.
2. Create a ``Workflow`` and call ``Workflow.start_at(now)``.
3. Persist the workflow, request first node, and stage events.
4. Commit and publish.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_requested_event import (
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.exceptions import TaskExecutionNotFound
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.application.execution.commands.workflow_commands import RunTaskerWorkflowCommand
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        UnitOfWork,
    )


class WorkflowRunTaskerHandler:
    """Creates a Workflow in RUNNING state and emits the first GraphNodeExecutionRequestedEvent."""

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
        """Persist a RUNNING workflow and request execution; return the workflow id."""
        task_execution_id = TaskExecutionId(run_tasker_workflow_command.task_execution_id)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            task_execution = await unit_of_work.repository(
                TaskExecutionRepository
            ).get_current_by_id(task_execution_id)
            if task_execution is None:
                raise TaskExecutionNotFound(run_tasker_workflow_command.task_execution_id)

            workflow = Workflow.new(
                id_=self._id_generator.new_id(WorkflowId),
                now=now,
            )
            task_execution.prepare_workspace(run_tasker_workflow_command.work_dir)
            task_execution.execute_in_workflow(workflow.id)
            await unit_of_work.repository(TaskExecutionRepository).save(task_execution)

            workflow.start_at(
                now=now,
                task_execution_id=task_execution_id,
            )

            graph_executions = await unit_of_work.repository(
                GraphExecutionRepository
            ).get_by_workflow_id(workflow.id)
            if graph_executions:
                nodes = await unit_of_work.repository(
                    GraphNodeExecutionRepository
                ).list_by_graph_execution_id(graph_executions[0].id)
                if nodes:
                    unit_of_work.stage_events(
                        [
                            GraphNodeExecutionRequestedEvent.now(
                                workflow_id=workflow.id,
                                graph_node_execution_id=nodes[0].id,
                                now=CreatedAt.from_datetime(now),
                            ),
                        ]
                    )

            await unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(workflow.pull_events())

        return workflow.id.value
