from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.error_description import ErrorDescription
from shell.domain.execution.value_objects.graph_node_execution_status import GraphNodeExecutionStatus

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_failed_event import (
        GraphNodeExecutionFailedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


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

    async def handle(
        self, graph_node_execution_failed_event: GraphNodeExecutionFailedEvent
    ) -> None:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(GraphNodeExecutionRepository).get_by_id(
                graph_node_execution_failed_event.node_id
            )
            if node is None:
                self._logger.warning(
                    "graph_node_execution_failed_handler.node_not_found",
                    node_id=graph_node_execution_failed_event.node_id.value,
                )
                return

            if node.status != GraphNodeExecutionStatus.RUNNING:
                self._logger.warning(
                    "graph_node_execution_failed_handler.node_not_running",
                    node_id=graph_node_execution_failed_event.node_id.value,
                    status=node.status.value,
                )
                return

            now = self._clock.now()
            node.fail(graph_node_execution_failed_event.error, now)
            await unit_of_work.repository(GraphNodeExecutionRepository).save(node)
            unit_of_work.stage_events(node.pull_events())
