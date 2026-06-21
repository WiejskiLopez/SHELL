"""PlannerSpawnsQueuedHandler — processes PlannerSpawnsQueuedEvent.

Marks the planner node as waiting for its spawned children.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.events import PlannerSpawnsQueuedEvent

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class PlannerSpawnsQueuedHandler:
    """Handles PlannerSpawnsQueuedEvent — marks planner node as waiting."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger

    async def handle(self, event: PlannerSpawnsQueuedEvent) -> None:
        """Mark the planner node workflow as waiting for children."""
        now = self._clock.now()

        async with self._uow as uow:
            parent_graph = await uow.graph_executions.get_by_id(
                event.parent_graph_execution_id,
            )
            if parent_graph is None:
                self._logger.warning(
                    "planner_spawns_queued.parent_graph_not_found",
                    parent_id=event.parent_graph_execution_id.value,
                )
                return

            parent_task = await uow.task_executions.get_by_id(
                parent_graph.task_execution_id,
            )
            if parent_task is None or parent_task.workflow_id is None:
                self._logger.warning(
                    "planner_spawns_queued.parent_no_workflow",
                    parent_graph_id=parent_graph.id.value,
                )
                return

            workflow = await uow.workflows.get_by_id(parent_task.workflow_id)
            if workflow is None:
                return

            workflow.wait_for_children(
                graph_node_execution_id=event.parent_graph_node_id,
                now=now,
            )

            try:
                await uow.workflows.save(workflow)
            except Exception:
                self._logger.warning(
                    "planner_spawns_queued.concurrent_modification",
                    workflow_id=workflow.id.value,
                )
                return

            uow.stage_events(workflow.pull_events())

            self._logger.info(
                "planner_spawns_queued.waiting",
                planner_node_id=event.parent_graph_node_id.value,
                spawn_count=event.spawn_count,
            )
