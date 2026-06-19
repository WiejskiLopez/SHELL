"""GraphNodeJoinExecutionHandler — handles join synchronization.

Subscribes to :class:`GraphNodeExecutionJoinReadyEvent` and advances
the workflow past the join node (or directly to the join target).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.events import GraphNodeExecutionJoinReadyEvent
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.services.graph_node_execution_navigator import NodeNavigator


class GraphNodeJoinExecutionHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        logger: Logger,
        navigator: NodeNavigator,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._logger = logger
        self._navigator = navigator

    async def handle(self, event: GraphNodeExecutionJoinReadyEvent) -> None:
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "graph_node_join_execution_handler.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            if workflow.status != Status.running():
                return

            graph_executions = await uow.graph_executions.get_by_workflow_id(
                workflow.id
            )
            if not graph_executions:
                return
            graph_execution = graph_executions[0]
            if graph_execution is None:
                return

            now = self._clock.now()
            next_nodes = list(
                self._navigator.next_after(graph_execution, event.join_node_execution_id)
            )

            if not next_nodes:
                workflow.finish(now)
            else:
                next_node = next_nodes[0]
                workflow.advance_and_request(
                    next_graph_node_execution_id=next_node.id, now=now
                )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
