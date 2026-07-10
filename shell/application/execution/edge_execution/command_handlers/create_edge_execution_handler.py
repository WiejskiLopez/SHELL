from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.edge_execution.edge_execution import EdgeExecution
from shell.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id import (
    EdgeDefinitionId,
)
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)

if TYPE_CHECKING:
    from shell.application.execution.edge_execution.commands.create_edge_execution_command import (
        CreateEdgeExecutionCommand,
    )
    from shell.platform.application.ports.identity import IdGenerator
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class CreateEdgeExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        identity: IdGenerator,
        time: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._identity = identity
        self._time = time

    async def handle(self, command: CreateEdgeExecutionCommand) -> str:
        from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
            NodeExecutionId,
        )

        now = self._time.now()
        edge_execution = EdgeExecution.new(
            id_=self._identity.new_id(EdgeExecutionId),
            edge_definition_id=EdgeDefinitionId(command.edge_definition_id),
            source_node_execution_id=NodeExecutionId(command.source_node_execution_id),
            target_node_execution_id=(
                NodeExecutionId(command.target_node_execution_id)
                if command.target_node_execution_id
                else None
            ),
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.repository(EdgeExecutionRepository).save(edge_execution)
            unit_of_work.stage_events(edge_execution.pull_events())
        return edge_execution.id.value
