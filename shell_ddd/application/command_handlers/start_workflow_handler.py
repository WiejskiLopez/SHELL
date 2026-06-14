"""StartWorkflowHandler — creates a new Workflow for a task.

Loads the task's Graph, transitions the Workflow to ``running`` via
``Workflow.start_at`` (anchoring the cursor on the first graph node), and
persists. Unlike :class:`RunTaskerWorkflowHandler` this handler does **not**
emit ``NodeExecutionRequested`` — it is the "prepare without auto-kickoff"
entrypoint used by the API and integration tests.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.exceptions import TaskNotFound, WorkflowHasNoNodes
from shell_ddd.domain.services.node_navigator import LinearNodeNavigator
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import StartWorkflowCommand
    from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork
    from shell_ddd.domain.services.node_navigator import NodeNavigator


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
        self._navigator: NodeNavigator = navigator or LinearNodeNavigator()

    async def handle(self, cmd: StartWorkflowCommand) -> str:
        now = self._clock.now()
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(TaskName(cmd.task_name))
            if task is None:
                raise TaskNotFound(cmd.task_name)

            graph = await uow.graphs.get_by_task_id(task.id)
            first_node = self._navigator.first(graph) if graph is not None else None
            if first_node is None:
                raise WorkflowHasNoNodes(cmd.task_name)

            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_name=cmd.task_name,
                now=now,
            )
            workflow.start_at(
                first_node_id=first_node.id,
                context=WorkflowExecutionContext.empty(),
                now=now,
            )
            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
            await uow.commit()
        return workflow.id.value
