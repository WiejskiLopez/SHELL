"""RunGraphNodeExecutionHandler — executes a node within a workflow using the appropriate strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.exceptions import WorkflowNotFound
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import RunGraphNodeExecutionCommand
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        NodeProcessRunner,
        NodeWorkspace,
        UnitOfWork,
    )
    from shell.application.execution.strategies.graph_node_execution_strategy import (
        GraphNodeExecutionStrategy,
    )


class RunGraphNodeExecutionHandler:
    """Executes a graph node execution via the registered GraphNodeExecutionStrategy for its mode.

    Appends a NodeResult to the owning Workflow aggregate, syncing node state and
    emitting GraphNodeExecutionCompletedEvent/GraphNodeExecutionFailedEvent via Workflow.record_graph_node_execution_result.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        workspace: NodeWorkspace,
        runner: NodeProcessRunner,
        strategy: GraphNodeExecutionStrategy,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._workspace = workspace
        self._runner = runner
        self._strategy = strategy

    async def handle(self, cmd: RunGraphNodeExecutionCommand) -> str:
        """Execute node and return NodeResult id."""
        wf_id = WorkflowId(cmd.workflow_id)
        graph_node_execution_id = GraphNodeExecutionId(cmd.graph_node_execution_id)
        now = self._clock.now()

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(wf_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            workflow.update_graph_node_execution_state(
                graph_node_execution_id, Status.running(), now=now
            )
            await uow.workflows.save(workflow)

        # Execute strategy (outside UoW — may take a long time)
        try:
            exec_result = await self._strategy.execute(
                graph_node_execution_id=cmd.graph_node_execution_id,
                workspace_path=cmd.workspace_path,
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

        async with self._uow as uow:
            wf = await uow.workflows.get_by_id(wf_id)
            if wf is None:
                raise WorkflowNotFound(cmd.workflow_id)
            result = wf.record_graph_node_execution_result(
                result_id=self._id_gen.new_graph_node_execution_result_id(),
                graph_node_execution_id=graph_node_execution_id,
                status=node_status,
                now=now,
                stdout=stdout,
                stderr=stderr,
                reason=failure_reason,
            )
            await uow.workflows.save(wf)
            uow.stage_events(wf.pull_events())

        return result.id.value
