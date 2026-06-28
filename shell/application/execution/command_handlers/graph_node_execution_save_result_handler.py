"""GraphNodeExecutionSaveResultHandler — saves a result state output for GraphNodeExecution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution_state import GraphNodeExecutionState
from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
    GraphNodeExecutionStateId,
)
from shell.domain.execution.exceptions import WorkflowNotFound
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.platform.commands import SaveGraphNodeExecutionResultCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


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

    async def handle(self, save_graph_node_execution_result_command: SaveGraphNodeExecutionResultCommand) -> str:
        graph_node_execution_id = GraphNodeExecutionId(save_graph_node_execution_result_command.graph_node_execution_id)
        workflow_id = WorkflowId(save_graph_node_execution_result_command.workflow_id)
        status = Status(save_graph_node_execution_result_command.status)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.workflow_repository.get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(save_graph_node_execution_result_command.workflow_id)

            node = await unit_of_work.graph_node_execution_repository.get_by_id(graph_node_execution_id)
            if node is not None:
                result_id = GraphNodeExecutionStateId.generate()
                state = GraphNodeExecutionState.create(
                    id_=result_id,
                    graph_node_execution_id=graph_node_execution_id,
                    direction=StateDirection.OUT,
                    payload={
                        "status": status.value,
                        "stdout": save_graph_node_execution_result_command.stdout or "",
                        "stderr": save_graph_node_execution_result_command.stderr or "",
                        "artifact_uri": save_graph_node_execution_result_command.artifact_uri or "",
                    },
                    now=now,
                )
                await unit_of_work.graph_node_execution_state_repository.save(state)
                await unit_of_work.workflow_repository.save(workflow)
                unit_of_work.stage_events(workflow.pull_events())

                return result_id.value

        return ""
