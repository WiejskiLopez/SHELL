"""WorkflowCompletedNotifyParentHandler — bridges sub-graph completion to parent.

Listens to WorkflowCompletedEvent. When a completed graph execution is a child
(has parent_graph_execution_id), queries the parent's children to determine
if all children are settled, then emits GraphExecutionSubGraphSettledEvent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_settled_event import (
    GraphExecutionSubGraphSettledEvent,
)
from shell.domain.execution.events import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.value_objects.graph_execution_status import GraphExecutionStatus

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class WorkflowCompletedNotifyParentHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._logger = logger

    async def handle(self, event: WorkflowCompletedEvent) -> None:
        async with self._uow as uow:
            graph_executions = await uow.graph_executions.get_by_workflow_id(
                event.workflow_id,
            )
            if not graph_executions:
                return
            graph_execution = graph_executions[0]

            if graph_execution.parent_graph_execution_id is None:
                return

            parent_id = graph_execution.parent_graph_execution_id
            parent_graph = await uow.graph_executions.get_by_id(parent_id)
            if parent_graph is None:
                self._logger.warning(
                    "workflow_completed_notify_parent_handler.parent_graph_not_found",
                    parent_graph_id=parent_id.value,
                )
                return

            children = await uow.graph_executions.get_by_parent_id(parent_id)
            all_settled = all(
                c.status in (GraphExecutionStatus.COMPLETED, GraphExecutionStatus.FAILED)
                for c in children
            )
            if not all_settled:
                return

            child_results: list[dict[str, Any]] = [
                {
                    "graph_execution_id": c.id.value,
                    "status": c.status.value,
                    "result": dict(c.state_output) if c.state_output else {},
                }
                for c in children
            ]

            parent_graph.absorb_child_results(child_results, event.occurred_at)
            parent_graph.append_event(
                GraphExecutionSubGraphSettledEvent.now(
                    parent_graph_execution_id=parent_id,
                    now=event.occurred_at,
                    child_results=child_results,
                )
            )

            await uow.graph_executions.save(parent_graph)
            uow.stage_events(parent_graph.pull_events())
