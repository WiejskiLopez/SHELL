"""GraphNodeExecutionFailedStateHandler — creates state on node failure.

Subscribes to GraphNodeExecutionFailedEvent. Creates a GraphNodeExecutionState
(direction=OUT) with the error payload. Modyfikuje tylko GraphNodeExecutionState.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_failed_event import (
    GraphNodeExecutionFailedEvent,
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


class GraphNodeExecutionFailedStateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(
        self, event: GraphNodeExecutionFailedEvent
    ) -> None:
        payload: dict[str, object] = {
            "status": "failed",
        }
        if event.error is not None:
            payload["error"] = event.error.value

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
