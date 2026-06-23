from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.graph_planning_started_event import (
    GraphPlanningStartedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class HandleGraphPlanningStarted:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger

    async def handle(self, event: GraphPlanningStartedEvent) -> None:
        async with self._uow as uow:
            graph_execution = await uow.graph_executions.get_by_id(event.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "handle_graph_planning_started.graph_not_found",
                    graph_execution_id=event.graph_execution_id.value,
                )
                return

            graph_execution.start_planning()
            await uow.graph_executions.save(graph_execution)
            uow.stage_events(graph_execution.pull_events())
