"""SaveNodeResultHandler."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.events.events import NodeCompleted, NodeFailed
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
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._events = events

    async def handle(self, cmd: SaveNodeResultCommand) -> str:
        node_id = NodeId(cmd.node_id)
        workflow_id = WorkflowId(cmd.workflow_id)
        status = Status(cmd.status)
        result = NodeResult.new(
            id_=self._id_gen.new_node_result_id(),
            node_id=node_id,
            workflow_id=workflow_id,
            status=status,
            stdout=cmd.stdout,
            stderr=cmd.stderr,
            artifact_uri=cmd.artifact_uri,
            now=self._clock.now(),
        )
        async with self._uow as uow:
            await uow.node_results.save(result)
            await uow.commit()
        if status == Status.done():
            await self._events.publish([NodeCompleted.now(node_id, workflow_id, result.id)])
        elif status == Status.failed():
            await self._events.publish([NodeFailed.now(node_id, workflow_id, cmd.stderr)])
        return result.id.value
