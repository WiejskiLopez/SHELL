"""NotifyParentOnChildCompletionHandler — bridges sub-graph completion to parent.

Listens to WorkflowCompletedEvent. When a completed graph execution is a child
(has parent_graph_execution_id), queries the parent's children to determine
if all children are settled, then emits SubGraphSettledEvent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_settled_event import (
    GraphExecutionSubGraphSettledEvent,
)
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
        WorkflowCompletedEvent,
    )
    from shell.domain.platform.ports.log import Logger


class NotifyParentOnChildCompletionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._logger = logger

    async def handle(self, event: WorkflowCompletedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            task_execution_id = event.task_execution_id
            if task_execution_id is None:
                task_executions = await unit_of_work.repository(
                    TaskExecutionRepository
                ).get_by_workflow_id(event.workflow_id)
                if not task_executions:
                    return
                task_execution_id = task_executions[0].id

            graph_executions = await unit_of_work.repository(
                GraphExecutionRepository
            ).get_by_task_execution_id(task_execution_id)
            if not graph_executions:
                return
            graph_execution = graph_executions[0]

            if graph_execution.parent_graph_execution_id is None:
                return

            parent_id = graph_execution.parent_graph_execution_id
            parent_graph = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                parent_id
            )
            if parent_graph is None:
                self._logger.warning(
                    "sub_graph.parent_graph_not_found",
                    parent_graph_id=parent_id.value,
                )
                return

            children = await unit_of_work.repository(GraphExecutionRepository).get_by_parent_id(
                parent_id
            )
            children_statuses = [c.status for c in children]
            if not parent_graph._check_all_children_settled(children_statuses):
                return

            parent_graph.append_event(
                GraphExecutionSubGraphSettledEvent.now(
                    parent_graph_execution_id=parent_id,
                    now=event.occurred_at,
                )
            )

            await unit_of_work.repository(GraphExecutionRepository).save(parent_graph)
            unit_of_work.stage_events(parent_graph.pull_events())
