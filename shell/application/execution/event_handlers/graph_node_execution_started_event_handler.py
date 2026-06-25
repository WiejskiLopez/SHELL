from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_started_event import (
    GraphNodeExecutionStartedEvent,
)
from shell.domain.execution.value_objects.node_role import NodeRole

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphNodeExecutionStartedEventHandler:
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

    async def handle(self, graph_node_execution_started_event: GraphNodeExecutionStartedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.graph_node_execution_repository.get_by_id(graph_node_execution_started_event.node_id)
            if node is None:
                self._logger.warning(
                    "handle_graph_node_execution_started.node_not_found",
                    node_id=graph_node_execution_started_event.node_id.value,
                )
                return

            node.start()
            await unit_of_work.graph_node_execution_repository.save(node)
            unit_of_work.stage_events(node.pull_events())
