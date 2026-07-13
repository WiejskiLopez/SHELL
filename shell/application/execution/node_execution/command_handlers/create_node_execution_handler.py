from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_order import NodeOrder
from shell.domain.execution.aggregates.node_execution.value_objects.node_role import NodeRole
from shell.domain.execution.aggregates.node_execution.value_objects.node_type import NodeType
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.execution.node_execution.commands.create_node_execution_command import (
        CreateNodeExecutionCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.identity import Identity  # type: ignore[attr-defined]
    from shell.platform.domain.ports.time import Time  # type: ignore[attr-defined]


class CreateNodeExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        identity: Identity,
        time: Time,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._identity = identity
        self._time = time

    async def handle(self, command: CreateNodeExecutionCommand) -> str:
        now = CreatedAt.from_datetime(self._time.now())
        graph_execution_id = GraphExecutionId(command.graph_execution_id)
        node_execution = NodeExecution.new(
            id=NodeExecutionId.generate(),
            graph_execution_id=graph_execution_id,
            node_definition_id=NodeDefinitionId(command.node_definition_id),
            role=NodeRole(command.role),
            position=NodeOrder(command.position),
            order=NodeOrder(command.position),
            mode=Mode(command.mode),
            node_type=NodeType(command.node_type),
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.repository(NodeExecutionRepository).save(node_execution)
            unit_of_work.stage_events(node_execution.pull_events())
        return node_execution.id.value
