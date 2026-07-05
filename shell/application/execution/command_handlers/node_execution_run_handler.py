"""NodeExecutionRunHandler — executes a node within a workflow using the appropriate strategy.

Modyfikuje tylko NodeExecution. NodeExecutionState jest tworzony przez
``NodeExecutionCompletedStateHandler`` / ``NodeExecutionFailedStateHandler``
reagujące na eventy z node'a.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.platform.value_objects.error_description import (
    ErrorDescription,
)
from shell.domain.execution.aggregates.workflow.exceptions.workflow_not_found import (
    WorkflowNotFound,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.value_objects.ids import NodeExecutionId, WorkflowId

if TYPE_CHECKING:
    from shell.application.execution.commands.node_execution_commands import (
        RunNodeExecutionCommand,
    )
    from shell.application.execution.strategies.node_execution_strategy import (
        NodeExecutionStrategy,
    )
    from shell.application.platform.ports.ports import (
        Clock,
        IdGenerator,
        NodeExecutionProcessRunner,
        NodeExecutionWorkspace,
        UnitOfWork,
    )


class NodeExecutionRunHandler:
    """Executes a graph node — marks node as RUNNING, executes via strategy, records result."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        workspace: NodeExecutionWorkspace,
        runner: NodeExecutionProcessRunner,
        strategy: NodeExecutionStrategy,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._workspace = workspace
        self._runner = runner
        self._strategy = strategy

    async def handle(self, command: RunNodeExecutionCommand) -> str:
        """Execute node and return node id."""
        workflow_id = WorkflowId(command.workflow_id)
        node_execution_id = NodeExecutionId(
            command.node_execution_id
        )

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(command.workflow_id)

            node = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_id
            )
            if node is None:
                raise WorkflowNotFound(command.node_execution_id)

            now = self._clock.now()
            node.start(now)
            await unit_of_work.repository(NodeExecutionRepository).save(node)
            unit_of_work.stage_events(node.pull_events())

        try:
            exec_result = await self._strategy.execute(
                node_execution_id=command.node_execution_id,
                workspace_path=command.workspace_path,
                runner=self._runner,
            )
        except Exception as exc:
            await self._record_failure(
                node_execution_id=node_execution_id,
                workflow_id=workflow_id,
                error=ErrorDescription(str(exc)),
            )
            return node_execution_id.value

        await self._record_success(
            node_execution_id=node_execution_id,
            workflow_id=workflow_id,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
        )
        return node_execution_id.value

    async def _record_success(
        self,
        *,
        node_execution_id: NodeExecutionId,
        workflow_id: WorkflowId,
        stdout: str,
        stderr: str,
    ) -> None:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_id
            )
            if node is None:
                return

            now = self._clock.now()
            node.complete({"stdout": stdout, "stderr": stderr}, now)
            await unit_of_work.repository(NodeExecutionRepository).save(node)
            unit_of_work.stage_events(node.pull_events())

    async def _record_failure(
        self,
        *,
        node_execution_id: NodeExecutionId,
        workflow_id: WorkflowId,
        error: ErrorDescription,
    ) -> None:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_id
            )
            if node is None:
                return

            now = self._clock.now()
            node.fail(error, now)
            await unit_of_work.repository(NodeExecutionRepository).save(node)
            unit_of_work.stage_events(node.pull_events())
