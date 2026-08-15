from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.platform.domain.value_objects.deleted_at import DeletedAt

if TYPE_CHECKING:
    from shell.execution_service.application.execution.node_execution.commands.delete_node_execution_command import (
        DeleteNodeExecutionCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class NodeExecutionNotFoundError(Exception):
    pass


class NodeExecutionAlreadyDeletedError(Exception):
    pass


class DeleteNodeExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: DeleteNodeExecutionCommand) -> None:
        node_execution_id = NodeExecutionId(command.node_execution_id)

        async with self._unit_of_work as unit_of_work:
            node_execution = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_id
            )
            if node_execution is None:
                raise NodeExecutionNotFoundError(
                    f"NodeExecution '{command.node_execution_id}' not found"
                )

            now = DeletedAt.from_datetime(self._clock.now())
            node_execution.mark_deleted(now)
            await unit_of_work.save(NodeExecutionRepository, node_execution)
