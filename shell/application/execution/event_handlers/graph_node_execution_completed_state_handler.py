"""GraphNodeExecutionCompletedStateHandler — creates state on node completion.

Subscribes to GraphNodeExecutionCompletedEvent. Creates a GraphNodeExecutionState
(direction=OUT) with the result payload. Modyfikuje tylko GraphNodeExecutionState.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.graph_node_execution_state.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
    GraphNodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
    GraphNodeExecutionStateId,
)
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.time import Clock


class GraphNodeExecutionCompletedStateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(
        self, event: GraphNodeExecutionCompletedEvent
    ) -> None:
        payload: dict[str, Any] = {
            "status": "done",
        }
        if event.result is not None:
            payload.update(event.result.to_dict())

        now = self._clock.now()
        async with self._unit_of_work as unit_of_work:
            state = GraphNodeExecutionState.create(
                id_=GraphNodeExecutionStateId.generate(),
                graph_node_execution_id=event.node_id,
                direction=StateDirection.OUT,
                payload=payload,
                now=now,
            )
            await unit_of_work.repository(GraphNodeExecutionStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())
