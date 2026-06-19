"""SaveGraphNodeExecutionResultHandler — appends a NodeResult to the owning Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.exceptions import WorkflowNotFound
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import SaveGraphNodeExecutionResultCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class SaveGraphNodeExecutionResultHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: SaveGraphNodeExecutionResultCommand) -> str:
        graph_node_execution_id = GraphNodeExecutionId(cmd.graph_node_execution_id)
        workflow_id = WorkflowId(cmd.workflow_id)
        status = Status(cmd.status)
        now = self._clock.now()

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            result = workflow.record_graph_node_execution_result(
                result_id=self._id_gen.new_graph_node_execution_result_id(),
                graph_node_execution_id=graph_node_execution_id,
                status=status,
                now=now,
                stdout=cmd.stdout,
                stderr=cmd.stderr,
                artifact_uri=cmd.artifact_uri,
            )
            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())

        return result.id.value
