"""StartWorkflowHandler — creates a new Workflow for a task_execution.

Loads the task's Graph, transitions the Workflow to ``running`` via
``Workflow.start_at`` (anchoring the cursor on the first graph node execution), and
persists. Unlike :class:`RunTaskerWorkflowHandler` this handler does **not**
emit ``GraphNodeExecutionRequestedEvent`` — it is the "prepare without auto-kickoff"
entrypoint used by the API and integration tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.exceptions import TaskExecutionNotFound, WorkflowHasNoNodes
from shell.domain.execution.services.graph_node_execution_navigator import LinearGraphNodeExecutionNavigator
from shell.domain.platform.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import StartWorkflowCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork
    from shell.domain.execution.services.graph_node_execution_navigator import NodeNavigator


class StartWorkflowHandler:
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

    async def handle(self, cmd: StartWorkflowCommand) -> str:
        now = self._clock.now()
        async with self._uow as uow:
            task_execution = await uow.task_executions.get_current_by_id(
                TaskExecutionId(cmd.task_execution_id)
            )
            if task_execution is None:
                raise TaskExecutionNotFound(cmd.task_execution_id)

            graph_execution = await uow.graph_executions.get_by_task_execution_id(task_execution.id)
            first_graph_node_execution = (
                self._navigator.first(graph_execution) if graph_execution is not None else None
            )
            if first_graph_node_execution is None:
                raise WorkflowHasNoNodes(cmd.task_execution_id)

            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_execution_id=TaskExecutionId(cmd.task_execution_id),
                now=now,
            )
            workflow.start_at(
                first_graph_node_execution_id=first_graph_node_execution.id,
                context=WorkflowExecutionContext.empty(),
                now=now,
            )
            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
        return workflow.id.value
