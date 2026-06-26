"""RunGraphNodeExecutionHandler — executes a node within a workflow using the appropriate strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.exceptions import WorkflowNotFound
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.execution.strategies.graph_node_execution_strategy import (
        GraphNodeExecutionStrategy,
    )
    from shell.application.platform.commands.commands import RunGraphNodeExecutionCommand
    from shell.application.platform.ports.ports import (
        Clock,
        GraphNodeExecutionProcessRunner,
        GraphNodeExecutionWorkspace,
        IdGenerator,
        UnitOfWork,
    )


class RunGraphNodeExecutionHandler:
    """Executes a graph node execution via the registered GraphNodeExecutionStrategy for its mode.

    Appends a NodeResult to the owning Workflow aggregate, syncing node state and
    emitting GraphNodeExecutionCompletedEvent/GraphNodeExecutionFailedEvent via Workflow.record_graph_node_execution_result.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        workspace: GraphNodeExecutionWorkspace,
        runner: GraphNodeExecutionProcessRunner,
        strategy: GraphNodeExecutionStrategy,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._workspace = workspace
        self._runner = runner
        self._strategy = strategy

    async def handle(self, run_graph_node_execution_command: RunGraphNodeExecutionCommand) -> str:
        """Execute node and return NodeResult id."""
        workflow_id = WorkflowId(run_graph_node_execution_command.workflow_id)
        graph_node_execution_id = GraphNodeExecutionId(run_graph_node_execution_command.graph_node_execution_id)
        now = self._clock.now()

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.workflow_repository.get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(run_graph_node_execution_command.workflow_id)

            await unit_of_work.workflow_repository.save(workflow)

        try:
            exec_result = await self._strategy.execute(
                graph_node_execution_id=run_graph_node_execution_command.graph_node_execution_id,
                workspace_path=run_graph_node_execution_command.workspace_path,
                runner=self._runner,
            )
            stdout = exec_result.stdout
            stderr = exec_result.stderr
            node_status = Status.done()
            failure_reason = ""
        except Exception as exc:
            stdout = ""
            stderr = str(exc)
            node_status = Status.failed()
            failure_reason = str(exc)

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.workflow_repository.get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(run_graph_node_execution_command.workflow_id)
            await unit_of_work.workflow_repository.save(workflow)
            unit_of_work.stage_events(workflow.pull_events())

        return ""
