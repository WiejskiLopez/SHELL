from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphNodeExecutionCompletedPropagateOutputHandler:
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

    async def handle(self, event: GraphNodeExecutionCompletedEvent) -> None:
        async with self._uow as uow:
            node = await uow.graph_node_executions.get_by_id(event.node_id)
            if node is None or node.graph_execution_id is None:
                self._logger.warning(
                    "graph_node_execution_completed_propagate_output_handler.node_not_found",
                    node_id=event.node_id.value,
                )
                return

            graph_execution = await uow.graph_executions.get_by_id(node.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "graph_node_execution_completed_propagate_output_handler.graph_not_found",
                    graph_execution_id=node.graph_execution_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "node_id": event.node_id.value,
                "role": event.role.value,
                "result": event.result,
            }
            graph_execution.add_state_input(output_payload, now)
            await uow.graph_executions.save(graph_execution)
            uow.stage_events(graph_execution.pull_events())
