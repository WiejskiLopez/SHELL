from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planning_started_event import (
    GraphExecutionPlanningStartedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphExecutionPlanningStartedEventHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._logger = logger

    async def handle(self, graph_execution_planning_started_event: GraphExecutionPlanningStartedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.graph_execution_repository.get_by_id(graph_execution_planning_started_event.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "handle_graph_planning_started.graph_not_found",
                    graph_execution_id=graph_execution_planning_started_event.graph_execution_id.value,
                )
                return

            graph_execution.start_planning()
            await unit_of_work.graph_execution_repository.save(graph_execution)
            unit_of_work.stage_events(graph_execution.pull_events())
