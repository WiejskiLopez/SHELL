"""PlannerResultHandler — processes NodeExecutionCompletedEvent for PLANNER nodes.

Subscribes to NodeExecutionCompletedEvent with role=PLANNER.
Delegates spawn and plan logic to GraphExecution domain methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionIdRef
from shell.domain.execution.value_objects.node_role import NodeRole

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_definition_provider import (
        GraphExecutionDefinitionProvider,
    )
    from shell.domain.execution.aggregates.node_execution.events.node_execution_completed_event import (
        NodeExecutionCompletedEvent,
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

    async def handle(
        self, node_execution_completed_event: NodeExecutionCompletedEvent
    ) -> None:
        if node_execution_completed_event.role != NodeRole.PLANNER:
            return

        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_completed_event.node_id
            )
            if node is None or node.graph_execution_id is None:
                self._logger.warning(
                    "planner_result_handler.node_not_found",
                    node_id=node_execution_completed_event.node_id.value,
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

            result: dict[str, Any] = node_execution_completed_event.result.to_dict()
            stage = result.get("stage", "")
            spawns: list[dict[str, Any]] = result.get("spawns", [])
            plan = result.get("plan", {})
            now = node_execution_completed_event.occurred_at

            for spawn in spawns:
                goal = spawn.get("goal", "")
                if not goal:
                    continue

                child_id = GraphExecutionId.generate()
                definition_id = ""
                try:
                    definition_id = await self._sub_graph_discovery.find_unique(goal)
                    await self._definition_provider.get_graph_definition(definition_id)
                except Exception:
                    self._logger.warning(
                        "planner_result_handler.definition_resolve_failed",
                        goal=goal,
                    )

                graph_execution.request_sub_graph_spawn(
                    child_graph_execution_id=child_id,
                    graph_definition_id=GraphDefinitionIdRef(definition_id or ""),
                    now=now.value,
                )

            if stage == "direct" and plan:
                graph_execution.plan_complete(plan=plan, now=now.value)

            await unit_of_work.repository(GraphExecutionRepository).save(graph_execution)
            unit_of_work.stage_events(list(graph_execution.pull_events()))

            self._logger.info(
                "planner_result_handler.processed",
                planner_node_id=node_execution_completed_event.node_id.value,
                spawn_count=len(spawns),
                stage=stage,
            )
