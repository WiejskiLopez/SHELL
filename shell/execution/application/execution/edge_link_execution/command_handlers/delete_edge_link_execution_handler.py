from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.execution.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.platform.domain.value_objects.deleted_at import DeletedAt

if TYPE_CHECKING:
    from shell.execution.application.execution.edge_link_execution.commands.delete_edge_link_execution_command import (
        DeleteEdgeLinkExecutionCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.log import Logger
    from shell.platform.domain.ports.time import Clock

from shell.execution.domain.execution.aggregates.edge_link_execution.exceptions.edge_link_execution_not_found_error import (
    EdgeLinkExecutionNotFoundError,
)


class DeleteEdgeLinkExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        time: Clock,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._time = time
        self._logger = logger

    async def handle(self, command: DeleteEdgeLinkExecutionCommand) -> None:
        now = DeletedAt.from_datetime(self._time.now())
        async with self._unit_of_work as unit_of_work:
            repo = unit_of_work.repository(EdgeLinkExecutionRepository)
            link = await repo.get_by_id(EdgeLinkExecutionId(command.id))
            if link is None:
                raise EdgeLinkExecutionNotFoundError(command.id)
            link.mark_deleted(now)
            await unit_of_work.save(EdgeLinkExecutionRepository, link)
