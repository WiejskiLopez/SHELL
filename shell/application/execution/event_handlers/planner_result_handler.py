"""PlannerResultHandler — processes GraphNodeExecutionCompletedEvent for PLANNER nodes.

Subscribes to GraphNodeExecutionCompletedEvent with role=PLANNER.
Calls GraphExecution.request_sub_graph_spawn() for each spawn entry,
or emits GraphPlannedEvent for direct plans.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.node_role import NodeRole

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_definition_provider import (
        GraphExecutionDefinitionProvider,
    )
    from shell.domain.execution.ports.sub_graph_discovery import SubGraphDiscovery
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class PlannerResultHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        logger: Logger,
        definition_provider: GraphExecutionDefinitionProvider,
        sub_graph_discovery: SubGraphDiscovery,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._logger = logger
        self._definition_provider = definition_provider
        self._sub_graph_discovery = sub_graph_discovery

    async def handle(self, graph_node_execution_completed_event: GraphNodeExecutionCompletedEvent) -> None:
        if graph_node_execution_completed_event.role != NodeRole.PLANNER:
            return

        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(GraphNodeExecutionRepository).get_by_id(graph_node_execution_completed_event.node_id)
            if node is None or node.graph_execution_id is None:
                self._logger.warning(
                    "planner_result_handler.node_not_found",
                    node_id=graph_node_execution_completed_event.node_id.value,
                )
                return

            graph_execution = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                node.graph_execution_id
            )
            if graph_execution is None:
                self._logger.warning(
                    "planner_result_handler.graph_not_found",
                    graph_execution_id=node.graph_execution_id.value,
                )
                return

            result: dict[str, Any] = graph_node_execution_completed_event.result.to_dict() if graph_node_execution_completed_event.result else {}
            stage = result.get("stage", "")
            spawns: list[dict[str, Any]] = result.get("spawns", [])
            plan = result.get("plan", {})
            now = graph_node_execution_completed_event.occurred_at

            for spawn in spawns:
                goal = spawn.get("goal", "")
                if not goal:
                    continue
                from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
                    GraphExecutionId as GEId,
                )

                child_id = GEId.generate()
                definition_id = ""
                expected_count = 0
                try:
                    definition_id = await self._sub_graph_discovery.find_unique(goal)
                    definition = await self._definition_provider.get_graph_definition(definition_id)
                    if definition is not None:
                        expected_count = len(definition.graph_node_execution_definitions)
                except Exception:
                    self._logger.warning(
                        "planner_result_handler.definition_resolve_failed",
                        goal=goal,
                    )
                from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_spawn_requested_event import (
                    GraphExecutionSubGraphSpawnRequestedEvent,
                )
                from shell.domain.execution.value_objects.graph_definition_id import (
                    GraphDefinitionIdRef,
                )

                graph_execution.append_event(
                    GraphExecutionSubGraphSpawnRequestedEvent.now(
                        parent_graph_execution_id=graph_execution.id,
                        child_graph_execution_id=child_id,
                        graph_definition_id=GraphDefinitionIdRef(definition_id or ""),
                        now=now,
                        state_input=None,
                    )
                )

            if stage == "direct" and plan:
                graph_execution.plan_complete(plan=plan, now=now.value)

            await unit_of_work.repository(GraphExecutionRepository).save(graph_execution)
            unit_of_work.stage_events(list(graph_execution.pull_events()))

            self._logger.info(
                "planner_result_handler.processed",
                planner_node_id=graph_node_execution_completed_event.node_id.value,
                spawn_count=len(spawns),
                stage=stage,
            )
