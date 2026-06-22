"""NotifyParentOnChildCompletionHandler — bridges sub-graph completion to parent.

Listens to WorkflowCompletedEvent. When a completed graph execution is a child
(has parent_graph_execution_id), queries the parent's children to determine
settled status via CrownScheduler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.events import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.exceptions import WorkflowConcurrentlyModified

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.ports.crown_scheduler import (
        CrownScheduler,
    )


class NotifyParentOnChildCompletionHandler:
    """Listens to child graph completion and notifies the parent via CrownScheduler."""

    def __init__(
        self,
        uow: UnitOfWork,
        logger: Logger,
        crown_scheduler: CrownScheduler,
    ) -> None:
        self._uow = uow
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

            if graph_execution.parent_graph_execution_id is None:
                return

            # Query settled status — no state stored, always fresh from repo
            result = await self._crown_scheduler.compute_settled_status(
                child_graph_execution_id=graph_execution.id,
                repo=uow.graph_executions,
            )
            if result is None:
                return

            self._logger.info(
                "sub_graph.child_completed",
                child_graph_id=graph_execution.id.value,
                parent_graph_id=result.parent_graph_execution_id.value,
                children_count=len(result.children_statuses),
            )

            # Load parent graph and absorb child results
            parent_graph = await uow.graph_executions.get_by_id(
                result.parent_graph_execution_id,
            )
            if parent_graph is None:
                self._logger.warning(
                    "sub_graph.parent_graph_not_found",
                    parent_graph_id=result.parent_graph_execution_id.value,
                )
                return

            combined_output: dict[str, Any] = {}
            for child_status in result.children_statuses:
                if child_status.result:
                    combined_output.update(child_status.result)
            parent_graph.absorb_child_results(combined_output)

            try:
                await uow.graph_executions.save(parent_graph)
            except WorkflowConcurrentlyModified:
                self._logger.warning(
                    "sub_graph.concurrent_modification",
                    parent_graph_id=parent_graph.id.value,
                )
                raise
