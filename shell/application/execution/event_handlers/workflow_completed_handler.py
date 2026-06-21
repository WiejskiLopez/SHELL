"""CrownSchedulerHandler — bridges sub-graph completion to parent notification.

Listens to WorkflowCompletedEvent and GraphNodeExecutionFailedEvent.
When a completed graph execution is a child (has parent_graph_execution_id),
notifies the CrownScheduler. If all children of a parent are done,
emits ChildGraphsCompletedEvent to unblock the parent workflow.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.exceptions import WorkflowConcurrentlyModified
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.ports.crown_scheduler import (
        CrownScheduler,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.events import WorkflowCompletedEvent
    from shell.domain.execution.value_objects.ids import (
        GraphNodeExecutionId,
    )


class NotifyParentOnChildCompletionHandler:
    """Listens to child graph completion and notifies the parent via CrownScheduler."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        crown_scheduler: CrownScheduler,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._crown_scheduler = crown_scheduler

    async def handle(self, event: WorkflowCompletedEvent) -> None:
        """Check if completed workflow belongs to a child graph and notify parent."""
        async with self._uow as uow:
            graph_executions = await uow.graph_executions.get_by_workflow_id(
                event.workflow_id,
            )
            if not graph_executions:
                return
            graph_execution = graph_executions[0]

            parent_graph_execution_id = graph_execution.parent_graph_execution_id
            if parent_graph_execution_id is None:
                return

            now = self._clock.now()
            child_graph_executions = await self._crown_scheduler.on_child_completed(
                child_graph_execution_id=graph_execution.id,
                result=graph_execution.state_output,
            )

            self._logger.info(
                "crown_scheduler.child_completed",
                child_graph_id=graph_execution.id.value,
                parent_graph_id=parent_graph_execution_id.value,
            )

            all_done = await self._crown_scheduler.has_all_children_completed(
                parent_graph_execution_id
            )
            if not all_done:
                return

            completed_ids = tuple(c.child_graph_execution_id for c in child_graph_executions)

            parent_graph = await uow.graph_executions.get_by_id(parent_graph_execution_id)
            if parent_graph is None:
                self._logger.warning(
                    "crown_scheduler.parent_graph_not_found",
                    parent_graph_id=parent_graph_execution_id.value,
                )
                return

            parent_task = await uow.task_executions.get_by_id(parent_graph.task_execution_id)
            if parent_task is None or parent_task.workflow_id is None:
                self._logger.warning(
                    "crown_scheduler.parent_no_workflow_id",
                    parent_graph_id=parent_graph_execution_id.value,
                )
                return

            parent_workflow = await uow.workflows.get_by_id(parent_task.workflow_id)
            if parent_workflow is None:
                self._logger.warning(
                    "crown_scheduler.parent_workflow_not_found",
                    parent_graph_id=parent_graph_execution_id.value,
                )
                return

            combined_output: dict[str, Any] = {}
            for child_execution_status in child_graph_executions:
                if child_execution_status.result:
                    combined_output.update(child_execution_status.result)
            parent_graph.absorb_child_results(combined_output)

            waiting_node = self._find_waiting_node(parent_workflow)
            if waiting_node is not None:
                parent_workflow.record_graph_node_execution_result(
                    result_id=self._id_gen.new_graph_node_execution_result_id(),
                    graph_node_execution_id=waiting_node,
                    status=Status.done(),
                    now=now,
                    stdout=str(combined_output),
                )

            parent_workflow.record_child_graphs_completed(
                parent_graph_execution_id=parent_graph_execution_id,
                completed_child_ids=completed_ids,
                combined_output=combined_output or None,
                now=now,
            )

            try:
                await uow.workflows.save(parent_workflow)
            except WorkflowConcurrentlyModified:
                self._logger.warning(
                    "crown_scheduler.concurrent_modification",
                    parent_workflow_id=parent_workflow.id.value,
                )
                raise
            await uow.graph_executions.save(parent_graph)
            uow.stage_events(parent_workflow.pull_events())

    @staticmethod
    def _find_waiting_node(
        workflow: Workflow,
    ) -> GraphNodeExecutionId | None:
        """Find the first node in WAITING state within the workflow."""
        for state in workflow.graph_node_execution_states:
            if state.status == Status.waiting():
                return state.graph_node_execution_id
        return None
