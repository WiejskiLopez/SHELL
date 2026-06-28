from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.commands.create_graph_node_execution_command import (
    CreateGraphNodeExecutionCommand,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.identity import Identity
    from shell.domain.platform.ports.time import Time


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

    async def handle(self, command: CreateGraphNodeExecutionCommand) -> None:
        now = self._time.now()
        node_execution = GraphNodeExecution.new(
            id=GraphNodeExecutionId.generate(),
            graph_execution_id=GraphExecutionId(command.graph_execution_id),
            now=now,
        )
        repo = self._unit_of_work.graph_node_execution_repository
        await repo.save(node_execution)
