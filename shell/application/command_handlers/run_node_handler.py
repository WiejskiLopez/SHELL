"""RunNodeHandler — executes a node within a workflow using the appropriate strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.exceptions import WorkflowNotFound
from shell.domain.value_objects.ids import NodeId, WorkflowId
from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.commands.commands import RunNodeCommand
    from shell.application.ports.ports import (
        Clock,
        IdGenerator,
        NodeProcessRunner,
        NodeWorkspace,
        UnitOfWork,
    )
    from shell.application.strategies.node_execution_strategy import NodeExecutionStrategy


class RunNodeHandler:
    """Executes a graph node via the registered NodeExecutionStrategy for its mode.

    Appends a NodeResult to the owning Workflow aggregate, syncing node state and
    emitting NodeCompleted/NodeFailed via Workflow.record_node_result.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        workspace: NodeWorkspace,
        runner: NodeProcessRunner,
        strategy: NodeExecutionStrategy,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._workspace = workspace
        self._runner = runner
        self._strategy = strategy

    async def handle(self, cmd: RunNodeCommand) -> str:
        """Execute node and return NodeResult id."""
        wf_id = WorkflowId(cmd.workflow_id)
        node_id = NodeId(cmd.node_id)
        now = self._clock.now()

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(wf_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            workflow.update_node_state(node_id, Status.running(), now=now)
            await uow.workflows.save(workflow)
            await uow.commit()

        # Execute strategy (outside UoW — may take a long time)
        try:
            exec_result = await self._strategy.execute(
                node_id=cmd.node_id,
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
            result = wf.record_node_result(
                result_id=self._id_gen.new_node_result_id(),
                node_id=node_id,
                status=node_status,
                now=now,
                stdout=stdout,
                stderr=stderr,
                reason=failure_reason,
            )
            await uow.workflows.save(wf)
            uow.stage_events(wf.pull_events())
            await uow.commit()

        return result.id.value
