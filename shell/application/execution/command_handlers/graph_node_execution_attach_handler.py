from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.commands.attach_graph_node_executions_command import (
    AttachGraphNodeExecutionsCommand,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.time import Time


class GraphExecutionNotFoundError(Exception):
    pass


class GraphNodeExecutionAttachHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        time: Time,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._time = time

    async def handle(self, command: AttachGraphNodeExecutionsCommand) -> None:
        now = self._time.now()
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                GraphExecutionId(command.graph_execution_id)
            )
            if graph_execution is None:
                raise GraphExecutionNotFoundError(
                    f"GraphExecution {command.graph_execution_id} not found"
                )

            for def_id, exec_id in command.graph_node_definition_executions.items():
                graph_execution.attach_node_execution(
                    node_definition_id=GraphNodeDefinitionId(def_id),
                    node_execution_id=GraphNodeExecutionId(exec_id),
                    now=now,
                )

            await unit_of_work.repository(GraphExecutionRepository).save(graph_execution)
            unit_of_work.stage_events(graph_execution.pull_events())
