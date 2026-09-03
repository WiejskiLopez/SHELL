from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.application.execution.node_execution.commands.create_node_execution_command import (
    CreateNodeExecutionCommand,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.execution_service.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.execution_service.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_definition_id_ref import (
    NodeDefinitionIdRef,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_order import (
    NodeOrder,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_type import (
    NodeType,
)
from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.identity import IdGenerator
    from shell.platform.domain.ports.time import Clock


class CreateNodeExecutionHandler(CommandHandler[CreateNodeExecutionCommand]):
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        identity: IdGenerator,
        time: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._identity = identity
        self._time = time

    async def handle(self, command: CreateNodeExecutionCommand) -> str:
        now = CreatedAt.from_datetime(self._time.now())
        graph_execution_id = GraphExecutionId(command.graph_execution_id)
        node_execution = NodeExecution.new(
            id=self._identity.new_id(NodeExecutionId),
            graph_execution_id=graph_execution_id,
            node_definition_id=NodeDefinitionIdRef(command.node_definition_id),
            order=NodeOrder(0),
            node_type=NodeType(command.node_type),
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(NodeExecutionRepository, node_execution)
        return node_execution.id.value
