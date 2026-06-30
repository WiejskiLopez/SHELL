from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planning_started_event import (
        GraphExecutionPlanningStartedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class GraphExecutionPlanningStartedHandler:
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

    async def handle(
        self, graph_execution_planning_started_event: GraphExecutionPlanningStartedEvent
    ) -> None:
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                graph_execution_planning_started_event.graph_execution_id
            )
            if graph_execution is None:
                self._logger.warning(
                    "graph_execution_planning_started_handler.graph_execution_not_found",
                    graph_execution_id=graph_execution_planning_started_event.graph_execution_id.value,
                )
                return

            now = self._clock.now()
            graph_execution.start_planning(now)
            await unit_of_work.repository(GraphExecutionRepository).save(graph_execution)
            unit_of_work.stage_events(graph_execution.pull_events())
