from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.application.execution.edge_execution.commands.change_edge_execution_command import (
    ChangeEdgeExecutionCommand,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.platform.application.ports.logger import Logger
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock

from shell.execution_service.domain.execution.aggregates.edge_execution.exceptions.edge_execution_not_found_error import (
    EdgeExecutionNotFoundError,
)


class ChangeEdgeExecutionHandler(CommandHandler[ChangeEdgeExecutionCommand]):
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        time: Clock,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._time = time
        self._logger = logger

    async def handle(self, command: ChangeEdgeExecutionCommand) -> None:
        from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
            NodeExecutionId,
        )

        now = OccurredAt.from_datetime(self._time.now())
        async with self._unit_of_work as unit_of_work:
            repo = unit_of_work.repository(EdgeExecutionRepository)
            edge = await repo.get_by_id(EdgeExecutionId(command.id))
            if edge is None:
                raise EdgeExecutionNotFoundError(command.id)
            edge.change_target(
                target_node_execution_id=(
                    NodeExecutionId(command.target_node_execution_id)
                    if command.target_node_execution_id
                    else None
                ),
                now=now,
            )
            await unit_of_work.save(EdgeExecutionRepository, edge)
