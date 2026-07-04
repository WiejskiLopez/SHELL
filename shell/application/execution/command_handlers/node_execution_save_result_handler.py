"""NodeExecutionSaveResultHandler — saves a result state output for NodeExecution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.node_execution_state import NodeExecutionState
from shell.domain.execution.aggregates.node_execution_state.repositories.node_execution_state_repository import (
    NodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
    NodeExecutionStateId,
)
from shell.domain.execution.value_objects.ids import NodeExecutionId
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.execution.commands.node_execution_commands import (
        SaveNodeExecutionResultCommand,
    )
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class NodeExecutionNotFoundError(Exception):
    pass


class NodeExecutionSaveResultHandler:
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
        self, save_node_execution_result_command: SaveNodeExecutionResultCommand
    ) -> str:
        node_execution_id = NodeExecutionId(
            save_node_execution_result_command.node_execution_id
        )
        status = Status(save_node_execution_result_command.status)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_id
            )
            if node is None:
                raise NodeExecutionNotFoundError(
                    f"NodeExecution {save_node_execution_result_command.node_execution_id} not found"
                )

            state_id = NodeExecutionStateId.generate()
            state = NodeExecutionState.create(
                id_=state_id,
                node_execution_id=node_execution_id,
                direction=StateDirection.OUT,
                payload={
                    "status": status.value,
                    "stdout": save_node_execution_result_command.stdout,
                    "stderr": save_node_execution_result_command.stderr,
                    "artifact_uri": save_node_execution_result_command.artifact_uri,
                },
                now=now,
            )
            await unit_of_work.repository(NodeExecutionStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())

            return state_id.value
