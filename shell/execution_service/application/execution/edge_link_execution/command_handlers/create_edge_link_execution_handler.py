from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
    EdgeLinkExecution,
)
from shell.execution_service.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.execution_service.application.execution.edge_link_execution.commands.create_edge_link_execution_command import (
        CreateEdgeLinkExecutionCommand,
    )
    from shell.platform.application.ports.identity import IdGenerator
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class CreateEdgeLinkExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        identity: IdGenerator,
        time: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._identity = identity
        self._time = time

    async def handle(self, command: CreateEdgeLinkExecutionCommand) -> str:
        from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
            EdgeExecutionId,
        )
        from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
            NodeExecutionId,
        )

        now = CreatedAt.from_datetime(self._time.now())
        link = EdgeLinkExecution.new(
            id_=self._identity.new_id(EdgeLinkExecutionId),
            node_execution_id=NodeExecutionId(command.node_execution_id),
            edge_execution_id=EdgeExecutionId(command.edge_execution_id),
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(EdgeLinkExecutionRepository, link)
        return link.id.value
