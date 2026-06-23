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


class HandleGraphNodeExecutionFailed:
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

    async def handle(self, event: GraphNodeExecutionFailedEvent) -> None:
        async with self._uow as uow:
            node = await uow.graph_node_executions.get_by_id(event.node_id)
            if node is None:
                self._logger.warning(
                    "handle_graph_node_execution_failed.node_not_found",
                    node_id=event.node_id.value,
                )
                return

            now = self._clock.now()
            error = event.error if event.error else ErrorDescription("unknown error")
            node.fail(error, now)
            await uow.graph_node_executions.save(node)
            uow.stage_events(node.pull_events())
