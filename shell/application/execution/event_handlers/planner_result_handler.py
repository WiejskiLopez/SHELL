"""PlannerResultHandler — processes PlannerResultEvent from PLANNER nodes.

Subscribes to PlannerResultEvent (emitted by GraphNodeExecutionWorker for
PLANNER-mode nodes with valid JSON output). For each event:
1. Saves stage in GraphNodeExecution.extra["planner_stage"]
2. Emits SubGraphSpawnRequestedEvent for each spawn entry
3. Emits PlannerSpawnsQueuedEvent with total spawn count
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.events import (
    PlannerResultEvent,
    PlannerSpawnsQueuedEvent,
    SubGraphSpawnRequestedEvent,
)
from shell.domain.platform.events import (
    DomainEvent,  # noqa: TC002 — DomainEvent używany jako klasa bazowa w isinstance() i konstruktorze eventów
)

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class PlannerResultHandler:
    """Processes PlannerResultEvent — saves stage, emits spawn events."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger

    async def handle(self, event: PlannerResultEvent) -> None:
        """Handle planner result — save stage, emit spawn events."""
        async with self._uow as uow:
            node = await uow.graph_node_executions.get_by_id(
                event.graph_node_execution_id,
            )
            if node is None:
                self._logger.warning(
                    "planner_result_handler.node_not_found",
                    node_id=event.graph_node_execution_id.value,
                )
                return

            # ── Save stage in planner node extra ────────────────────────────
            if event.stage:
                node.extra["planner_stage"] = event.stage
                await uow.graph_node_executions.save(node)

            # ── Collect events to stage ─────────────────────────────────────
            staged_events: list[DomainEvent] = []

            # ── Emit SubGraphSpawnRequestedEvent for each spawn entry ───────
            for query in event.spawn:
                if not query or not query.strip():
                    continue
                staged_events.append(
                    SubGraphSpawnRequestedEvent.now(
                        query=query.strip(),
                        parent_graph_execution_id=event.graph_execution_id,
                        parent_graph_node_id=node.id,
                        now=event.occurred_at,
                    )
                )

            # ── Emit PlannerSpawnsQueuedEvent with total count ──────────────
            staged_events.append(
                PlannerSpawnsQueuedEvent.now(
                    parent_graph_execution_id=event.graph_execution_id,
                    parent_graph_node_id=node.id,
                    spawn_count=len(event.spawn),
                    now=event.occurred_at,
                )
            )

            # ── Stage all events at once ────────────────────────────────────
            if staged_events:
                uow.stage_events(staged_events)

            self._logger.info(
                "planner_result_handler.processed",
                planner_node_id=event.graph_node_execution_id.value,
                spawn_count=len(event.spawn),
                has_stage=bool(event.stage),
            )
