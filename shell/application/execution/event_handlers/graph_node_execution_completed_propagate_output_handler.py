from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphNodeExecutionCompletedPropagateOutputHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._logger = logger

    async def handle(self, graph_node_execution_completed_event: GraphNodeExecutionCompletedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            node = await unit_of_work.graph_node_execution_repository.get_by_id(graph_node_execution_completed_event.node_id)
            if node is None or node.graph_execution_id is None:
                self._logger.warning(
                    "graph_node_execution_completed_propagate_output_handler.node_not_found",
                    node_id=graph_node_execution_completed_event.node_id.value,
                )
                return

            graph_execution = await unit_of_work.graph_execution_repository.get_by_id(node.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "graph_node_execution_completed_propagate_output_handler.graph_not_found",
                    graph_execution_id=node.graph_execution_id.value,
                )
                return

            now = self._clock.now()
            output_payload: dict[str, Any] = {
                "node_id": graph_node_execution_completed_event.node_id.value,
                "role": graph_node_execution_completed_event.role.value,
                "result": graph_node_execution_completed_event.result,
            }
            state = GraphExecutionState.create(
                id_=GraphExecutionStateId.generate(),
                graph_execution_id=graph_execution.id,
                direction=StateDirection.IN,
                now=now,
            )
            state.patch(output_payload)
            await unit_of_work.graph_execution_state_repository.save(state)
            unit_of_work.stage_events(state.pull_events())
