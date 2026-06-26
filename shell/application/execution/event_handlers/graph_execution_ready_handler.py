from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_ready_event import (
    GraphExecutionReadyEvent,
)

if TYPE_CHECKING:
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphExecutionReadyHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._logger = logger

    async def handle(self, event: GraphExecutionReadyEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            graph = await unit_of_work.graph_execution_repository.get_by_id(event.graph_execution_id)
            if graph is None:
                self._logger.warning(
                    "ready_handler.graph_not_found",
                    graph_id=event.graph_execution_id.value,
                )
                return

            self._logger.info(
                "ready_handler.ready_received",
                graph_id=event.graph_execution_id.value,
                child_id=event.child_graph_execution_id.value,
            )
