from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.execution.commands.create_graph_node_execution_command import (
        CreateGraphNodeExecutionCommand,
    )
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.identity import Identity  # type: ignore[attr-defined]
    from shell.domain.platform.ports.time import Time  # type: ignore[attr-defined]


class GraphNodeExecutionCreateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        identity: Identity,
        time: Time,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._identity = identity
        self._time = time

    async def handle(self, command: CreateGraphNodeExecutionCommand) -> str:
        now = self._time.now()
        graph_execution_id = GraphExecutionId(command.graph_execution_id)
        node_execution = GraphNodeExecution.new(
            id=GraphNodeExecutionId.generate(),
            graph_execution_id=graph_execution_id,
            parent_graph_execution_id=graph_execution_id,
            node_definition_id=GraphNodeDefinitionId(command.graph_node_definition_id),
            role=NodeRole(command.role),
            position=NodeOrder(command.position),
            mode=Mode(command.mode),
            node_type=NodeType(command.node_type),
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.repository(GraphNodeExecutionRepository).save(node_execution)
            unit_of_work.stage_events(node_execution.pull_events())
        return node_execution.id.value
