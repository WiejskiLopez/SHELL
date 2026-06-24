from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_failed_event import (
    GraphNodeExecutionFailedEvent,
)
from shell.domain.execution.value_objects.error_description import ErrorDescription

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphNodeExecutionFailedHandler:
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

    async def handle(self, event: GraphNodeExecutionFailedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.graph_node_executions.get_by_id(event.node_id)
            if node is None:
                self._logger.warning(
                    "graph_node_execution_failed_handler.node_not_found",
                    node_id=event.node_id.value,
                )
                return

            now = self._clock.now()
            error = event.error if event.error else ErrorDescription("unknown error")
            node.fail(error, now)
            await unit_of_work.graph_node_executions.save(node)
            unit_of_work.stage_events(node.pull_events())
