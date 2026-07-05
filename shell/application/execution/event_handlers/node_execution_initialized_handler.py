from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.node_execution.events.node_execution_initialized_event import (
        NodeExecutionInitializedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class NodeExecutionInitializedHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._logger = logger

    async def handle(self, event: NodeExecutionInitializedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            parent = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                event.graph_execution_id
            )
            if parent is None:
                self._logger.warning(
                    "node_initialized.parent_not_found",
                    parent_id=event.graph_execution_id.value,
                )
                return

            self._logger.info(
                "node_initialized.confirmed",
                node_id=event.node_id.value,
                parent_id=event.graph_execution_id.value,
            )
