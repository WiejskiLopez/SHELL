from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_settled_event import (
    GraphExecutionSubGraphSettledEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphExecutionSubGraphSettledPropagateResultsHandler:
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

    async def handle(self, event: GraphExecutionSubGraphSettledEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            parent_graph = await unit_of_work.graph_executions.get_by_id(
                event.parent_graph_execution_id
            )
            if parent_graph is None:
                self._logger.warning(
                    "graph_execution_sub_graph_settled_propagate_results_handler.parent_not_found",
                    parent_id=event.parent_graph_execution_id.value,
                )
                return

            now = self._clock.now()
            parent_graph.absorb_child_results(event.child_results, now)
            await unit_of_work.graph_executions.save(parent_graph)
            unit_of_work.stage_events(parent_graph.pull_events())
