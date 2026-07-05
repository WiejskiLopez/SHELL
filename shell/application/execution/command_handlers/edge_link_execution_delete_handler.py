from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)

if TYPE_CHECKING:
    from shell.application.execution.commands.delete_edge_link_execution_command import (
        DeleteEdgeLinkExecutionCommand,
    )
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock

from shell.domain.execution.aggregates.edge_link_execution.exceptions.edge_link_execution_not_found_error import (
    EdgeLinkExecutionNotFoundError,
)


class EdgeLinkExecutionDeleteHandler:
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
        now = self._time.now()
        async with self._unit_of_work as unit_of_work:
            repo = unit_of_work.repository(EdgeLinkExecutionRepository)
            link = await repo.get_by_id(EdgeLinkExecutionId(command.id))
            if link is None:
                raise EdgeLinkExecutionNotFoundError(command.id)
            link.mark_deleted(now)
            await repo.save(link)
            unit_of_work.stage_events(link.pull_events())
