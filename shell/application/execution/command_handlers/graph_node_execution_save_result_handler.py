"""GraphNodeExecutionSaveResultHandler — saves a result state output for GraphNodeExecution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution_state import GraphNodeExecutionState
from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
    GraphNodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
    GraphNodeExecutionStateId,
)
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.execution.commands.graph_node_execution_commands import (
        SaveGraphNodeExecutionResultCommand,
    )
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class GraphNodeExecutionNotFoundError(Exception):
    pass


class GraphNodeExecutionSaveResultHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(
        self, save_graph_node_execution_result_command: SaveGraphNodeExecutionResultCommand
    ) -> str:
        graph_node_execution_id = GraphNodeExecutionId(
            save_graph_node_execution_result_command.graph_node_execution_id
        )
        status = Status(save_graph_node_execution_result_command.status)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(GraphNodeExecutionRepository).get_by_id(
                graph_node_execution_id
            )
            if node is None:
                raise GraphNodeExecutionNotFoundError(
                    f"GraphNodeExecution {save_graph_node_execution_result_command.graph_node_execution_id} not found"
                )

            result_id = GraphNodeExecutionStateId.generate()
            state = GraphNodeExecutionState.create(
                id_=result_id,
                graph_node_execution_id=graph_node_execution_id,
                direction=StateDirection.OUT,
                payload={
                    "status": status.value,
                    "stdout": save_graph_node_execution_result_command.stdout,
                    "stderr": save_graph_node_execution_result_command.stderr,
                    "artifact_uri": save_graph_node_execution_result_command.artifact_uri,
                },
                now=now,
            )
            await unit_of_work.repository(GraphNodeExecutionStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())

            return result_id.value
