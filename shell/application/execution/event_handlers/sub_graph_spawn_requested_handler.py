"""SubGraphSpawnRequestedHandler — processes SubGraphSpawnRequestedEvent.

Receives spawn requests from PlannerResultHandler and:
1. Finds the best matching GraphDefinition via SubGraphDiscovery
2. Spawns a child GraphExecution via SubGraphExecutionService
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.events import (
    SubGraphSpawnRequestedEvent,  # noqa: TC002 — SubGraphSpawnRequestedEvent używany w sygnaturze handle() handlera
)

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.ports.sub_graph_discovery import SubGraphDiscovery
    from shell.domain.execution.services.sub_graph_execution_service import (
        SubGraphExecutionService,
    )


class SubGraphSpawnRequestedHandler:
    """Handles SubGraphSpawnRequestedEvent — discovery + spawn."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        logger: Logger,
        discovery: SubGraphDiscovery,
        sub_graph_service: SubGraphExecutionService,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger
        self._discovery = discovery
        self._sub_graph_service = sub_graph_service

    async def handle(self, event: SubGraphSpawnRequestedEvent) -> None:
        """Handle spawn request — find definition and spawn child graph."""
        async with self._uow as uow:
            parent_graph = await uow.graph_executions.get_by_id(
                event.parent_graph_execution_id,
            )
            if parent_graph is None:
                self._logger.warning(
                    "sub_graph_spawn_requested.parent_graph_not_found",
                    parent_id=event.parent_graph_execution_id.value,
                )
                return

            parent_node = await uow.graph_node_executions.get_by_id(
                event.parent_graph_node_id,
            )
            if parent_node is None:
                self._logger.warning(
                    "sub_graph_spawn_requested.parent_node_not_found",
                    node_id=event.parent_graph_node_id.value,
                )
                return

            # ── Discovery: find best GraphDefinition by query ────────────────
            try:
                definition_id = await self._discovery.find_unique(event.query)
            except Exception as exc:
                self._logger.error(
                    "sub_graph_spawn_requested.discovery_failed",
                    query=event.query,
                    error=str(exc),
                )
                return

            # ── Spawn child GraphExecution ──────────────────────────────────
            try:
                child = await self._sub_graph_service.spawn(
                    parent_graph_execution=parent_graph,
                    parent_tasker_node=parent_node,
                    graph_definition_id=definition_id,
                    state_input=parent_graph.state_input,
                    correlation_id=parent_graph.correlation_id,
                    uow=uow,
                )
            except Exception as exc:
                self._logger.error(
                    "sub_graph_spawn_requested.spawn_failed",
                    definition_id=definition_id,
                    query=event.query,
                    error=str(exc),
                )
                return

            self._logger.info(
                "sub_graph_spawn_requested.spawned",
                child_graph_id=child.id.value,
                parent_graph_id=parent_graph.id.value,
                definition_id=definition_id,
                query=event.query,
            )
