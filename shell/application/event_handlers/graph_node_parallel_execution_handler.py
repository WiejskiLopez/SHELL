"""GraphNodeParallelExecutionHandler — fans out parallel node execution requests.

Subscribes to :class:`GraphNodeParallelExecutionRequestedEvent` and emits
individual :class:`GraphNodeExecutionRequestedEvent` for each target node.
The workflow cursor stays on the fork node while parallel children execute.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.events.events import (
    GraphNodeExecutionRequestedEvent,
    GraphNodeParallelExecutionRequestedEvent,
)
from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.ports.logging import Logger
    from shell.application.ports.time import Clock
    from shell.application.ports.unit_of_work import UnitOfWork


class GraphNodeParallelExecutionHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger

    async def handle(self, event: GraphNodeParallelExecutionRequestedEvent) -> None:
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "graph_node_parallel_execution_handler.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            if workflow.status != Status.running():
                self._logger.debug(
                    "graph_node_parallel_execution_handler.skip_non_running",
                    workflow_id=workflow.id.value,
                    status=workflow.status.value,
                )
                return

            now = self._clock.now()
            for target_id in event.parallel_target_node_ids:
                workflow.update_graph_node_execution_state(target_id, Status.running(), now=now)
                workflow.append_event(
                    GraphNodeExecutionRequestedEvent.now(
                        workflow_id=event.workflow_id,
                        graph_node_execution_id=target_id,
                        now=now,
                    )
                )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
