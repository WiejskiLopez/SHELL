"""SaveGraphNodeExecutionResultHandler — appends a result state output to GraphNodeExecution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
    GraphNodeExecutionStateOutput,
)
from shell.domain.execution.exceptions import WorkflowNotFound
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import SaveGraphNodeExecutionResultCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class SaveGraphNodeExecutionResultHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: SaveGraphNodeExecutionResultCommand) -> str:
        graph_node_execution_id = GraphNodeExecutionId(command.graph_node_execution_id)
        workflow_id = WorkflowId(command.workflow_id)
        status = Status(command.status)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.workflows.get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(command.workflow_id)

            node = await unit_of_work.graph_node_executions.get_by_id(graph_node_execution_id)
            if node is not None:
                result_id = self._id_generator.new_graph_node_execution_result_id()
                output = GraphNodeExecutionStateOutput.create(
                    id_=result_id,
                    graph_node_execution_id=graph_node_execution_id,
                    payload={
                        "status": status.value,
                        "stdout": command.stdout or "",
                        "stderr": command.stderr or "",
                        "artifact_uri": command.artifact_uri or "",
                    },
                    now=now,
                )
                if hasattr(node, "output_states") and hasattr(node, "add_output_state"):
                    node.add_output_state(output)
                await unit_of_work.graph_node_executions.save(node)
                await unit_of_work.workflows.save(workflow)
                unit_of_work.stage_events(workflow.pull_events())

                return result_id.value

        return ""
