"""GraphNodeExecutionCompletedPlannerHandler — processes GraphNodeExecutionCompletedEvent for PLANNER nodes.

Subscribes to GraphNodeExecutionCompletedEvent with role=PLANNER.
Emits GraphExecutionSpawnedEvent for each spawn entry, or GraphExecutionPlannedEvent for direct plans.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planned_event import (
    GraphExecutionPlannedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_spawned_event import (
    GraphExecutionSpawnedEvent,
)
from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.value_objects.node_role import NodeRole

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphNodeExecutionCompletedPlannerHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._logger = logger

    async def handle(self, graph_node_execution_completed_event: GraphNodeExecutionCompletedEvent) -> None:
        if graph_node_execution_completed_event.role != NodeRole.PLANNER:
            return

        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.graph_node_execution_repository.get_by_id(graph_node_execution_completed_event.node_id)
            if node is None or node.graph_execution_id is None:
                self._logger.warning(
                    "graph_node_execution_completed_planner_handler.node_not_found",
                    node_id=graph_node_execution_completed_event.node_id.value,
                )
                return

            graph_execution = await unit_of_work.graph_execution_repository.get_by_id(
                node.graph_execution_id
            )
            if graph_execution is None:
                self._logger.warning(
                    "graph_node_execution_completed_planner_handler.graph_not_found",
                    graph_execution_id=node.graph_execution_id.value,
                )
                return

            result = graph_node_execution_completed_event.result or {}
            stage = result.get("stage", "")
            spawns: list[dict[str, Any]] = result.get("spawns", [])
            plan = result.get("plan", {})

            staged_events: list[Any] = []

            for spawn in spawns:
                goal = spawn.get("goal", "")
                if not goal:
                    continue
                from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
                    GraphExecutionId,
                )
                child_id = GraphExecutionId.generate()
                staged_events.append(
                    GraphExecutionSpawnedEvent.now(
                        parent_graph_execution_id=graph_execution.id,
                        child_graph_execution_id=child_id,
                        goal=goal,
                        now=graph_node_execution_completed_event.occurred_at,
                    )
                )

            if stage == "direct" and plan:
                staged_events.append(
                    GraphExecutionPlannedEvent.now(
                        graph_execution_id=graph_execution.id,
                        plan=plan,
                        now=graph_node_execution_completed_event.occurred_at,
                    )
                )

            if staged_events:
                unit_of_work.stage_events(staged_events)

            self._logger.info(
                "graph_node_execution_completed_planner_handler.processed",
                planner_node_id=graph_node_execution_completed_event.node_id.value,
                spawn_count=len(spawns),
                stage=stage,
            )
