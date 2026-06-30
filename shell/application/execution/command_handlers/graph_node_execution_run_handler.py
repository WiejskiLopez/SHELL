"""GraphNodeExecutionRunHandler — executes a node within a workflow using the appropriate strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution_state.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
    GraphNodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
    GraphNodeExecutionStateId,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.exceptions import WorkflowNotFound
from shell.domain.execution.value_objects.error_description import ErrorDescription
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.execution.commands.graph_node_execution_commands import (
        RunGraphNodeExecutionCommand,
    )
    from shell.application.execution.strategies.graph_node_execution_strategy import (
        GraphNodeExecutionStrategy,
    )
    from shell.application.platform.ports.ports import (
        Clock,
        GraphNodeExecutionProcessRunner,
        GraphNodeExecutionWorkspace,
        IdGenerator,
        UnitOfWork,
    )


class GraphNodeExecutionRunHandler:
    """Executes a graph node — marks node as RUNNING, executes via strategy, records result as state."""

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
        """Execute node and return result state id."""
        workflow_id = WorkflowId(run_graph_node_execution_command.workflow_id)
        graph_node_execution_id = GraphNodeExecutionId(
            run_graph_node_execution_command.graph_node_execution_id
        )

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(run_graph_node_execution_command.workflow_id)

            node = await unit_of_work.repository(GraphNodeExecutionRepository).get_by_id(
                graph_node_execution_id
            )
            if node is None:
                raise WorkflowNotFound(run_graph_node_execution_command.graph_node_execution_id)

            now = self._clock.now()
            node.start(now)
            await unit_of_work.repository(GraphNodeExecutionRepository).save(node)
            unit_of_work.stage_events(node.pull_events())

        try:
            exec_result = await self._strategy.execute(
                graph_node_execution_id=run_graph_node_execution_command.graph_node_execution_id,
                workspace_path=run_graph_node_execution_command.workspace_path,
                runner=self._runner,
            )
        except Exception as exc:
            return await self._record_failure(
                graph_node_execution_id=graph_node_execution_id,
                workflow_id=workflow_id,
                error=ErrorDescription(str(exc)),
            )

        return await self._record_success(
            graph_node_execution_id=graph_node_execution_id,
            workflow_id=workflow_id,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
        )

    async def _record_success(
        self,
        *,
        graph_node_execution_id: GraphNodeExecutionId,
        workflow_id: WorkflowId,
        stdout: str,
        stderr: str,
    ) -> str:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(GraphNodeExecutionRepository).get_by_id(
                graph_node_execution_id
            )
            if node is None:
                return ""

            now = self._clock.now()
            node.complete({"stdout": stdout, "stderr": stderr}, now)
            await unit_of_work.repository(GraphNodeExecutionRepository).save(node)

            result_id = GraphNodeExecutionStateId.generate()
            state = GraphNodeExecutionState.create(
                id_=result_id,
                graph_node_execution_id=graph_node_execution_id,
                direction=StateDirection.OUT,
                payload={
                    "status": "done",
                    "stdout": stdout,
                    "stderr": stderr,
                },
                now=now,
            )
            await unit_of_work.repository(GraphNodeExecutionStateRepository).save(state)

            unit_of_work.stage_events(node.pull_events())
            return result_id.value

    async def _record_failure(
        self,
        *,
        graph_node_execution_id: GraphNodeExecutionId,
        workflow_id: WorkflowId,
        error: ErrorDescription,
    ) -> str:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(GraphNodeExecutionRepository).get_by_id(
                graph_node_execution_id
            )
            if node is None:
                return ""

            now = self._clock.now()
            node.fail(error, now)
            await unit_of_work.repository(GraphNodeExecutionRepository).save(node)

            result_id = GraphNodeExecutionStateId.generate()
            state = GraphNodeExecutionState.create(
                id_=result_id,
                graph_node_execution_id=graph_node_execution_id,
                direction=StateDirection.OUT,
                payload={
                    "status": "failed",
                    "error": error.value,
                },
                now=now,
            )
            await unit_of_work.repository(GraphNodeExecutionStateRepository).save(state)

            unit_of_work.stage_events(node.pull_events())
            return result_id.value
