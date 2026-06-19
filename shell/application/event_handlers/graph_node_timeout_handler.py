"""GraphNodeTimeoutHandler — handles node execution timeouts.

Subscribes to :class:`GraphNodeExecutionTimedOutEvent` and marks
the timed-out node as failed if it hasn't completed yet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.events.events import GraphNodeExecutionTimedOutEvent
from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.ports.identity import IdGenerator
    from shell.application.ports.logging import Logger
    from shell.application.ports.time import Clock
    from shell.application.ports.unit_of_work import UnitOfWork


class GraphNodeTimeoutHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger

    async def handle(self, event: GraphNodeExecutionTimedOutEvent) -> None:
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                return

            if workflow.status != Status.running():
                return

            state = workflow.get_graph_node_execution_state(event.graph_node_execution_id)
            if state is None or state.status != Status.running():
                return

            now = self._clock.now()
            workflow.record_graph_node_execution_result(
                result_id=self._id_gen.new_graph_node_execution_result_id(),
                graph_node_execution_id=event.graph_node_execution_id,
                status=Status.failed(),
                now=now,
                stdout="",
                stderr=f"Node timed out after {event.timeout_seconds}s",
                reason=f"timeout after {event.timeout_seconds}s",
            )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
