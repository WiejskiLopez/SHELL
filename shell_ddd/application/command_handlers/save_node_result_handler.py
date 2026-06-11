"""SaveNodeResultHandler — appends a NodeResult to the owning Workflow aggregate."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.exceptions import WorkflowNotFound
from shell_ddd.domain.value_objects.ids import NodeId, WorkflowId
from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import SaveNodeResultCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, IdGenerator, UnitOfWork


class SaveNodeResultHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._event_publisher = event_publisher

    async def handle(self, cmd: SaveNodeResultCommand) -> str:
        node_id = NodeId(cmd.node_id)
        workflow_id = WorkflowId(cmd.workflow_id)
        status = Status(cmd.status)
        now = self._clock.now()

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            result = workflow.record_node_result(
                result_id=self._id_gen.new_node_result_id(),
                node_id=node_id,
                status=status,
                now=now,
                stdout=cmd.stdout,
                stderr=cmd.stderr,
                artifact_uri=cmd.artifact_uri,
            )
            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
            await uow.commit()

        await self._event_publisher.publish(uow.events)
        return result.id.value
