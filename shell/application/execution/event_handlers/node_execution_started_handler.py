from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.value_objects.node_execution_status import (
    NodeExecutionStatus,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.node_execution.events.node_execution_started_event import (
        NodeExecutionStartedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class NodeExecutionStartedHandler:
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
        self, node_execution_started_event: NodeExecutionStartedEvent
    ) -> None:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_started_event.node_id
            )
            if node is None:
                self._logger.warning(
                    "node_execution_started_handler.node_not_found",
                    node_id=node_execution_started_event.node_id.value,
                )
                return

            if node.status != NodeExecutionStatus.PENDING:
                self._logger.warning(
                    "node_execution_started_handler.node_already_started",
                    node_id=node_execution_started_event.node_id.value,
                    status=node.status.value,
                )
                return

            now = self._clock.now()
            node.start(now)
            await unit_of_work.repository(NodeExecutionRepository).save(node)
            unit_of_work.stage_events(node.pull_events())
