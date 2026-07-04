"""NodeExecutionCompletedStateHandler — creates state on node completion.

Subscribes to NodeExecutionCompletedEvent. Creates a NodeExecutionState
(direction=OUT) with the result payload. Modyfikuje tylko NodeExecutionState.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.node_execution_state.node_execution_state import (
    NodeExecutionState,
)
from shell.domain.execution.aggregates.node_execution_state.repositories.node_execution_state_repository import (
    NodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
    NodeExecutionStateId,
)
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.node_execution.events.node_execution_completed_event import (
        NodeExecutionCompletedEvent,
    )
    from shell.domain.platform.ports.time import Clock


class NodeExecutionCompletedStateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(
        self, event: NodeExecutionCompletedEvent
    ) -> None:
        payload: dict[str, Any] = {
            "status": "done",
        }
        if event.result is not None:
            payload.update(event.result.to_dict())

        now = self._clock.now()
        async with self._unit_of_work as unit_of_work:
            state = NodeExecutionState.create(
                id_=NodeExecutionStateId.generate(),
                node_execution_id=event.node_id,
                direction=StateDirection.OUT,
                payload=payload,
                now=now,
            )
            await unit_of_work.repository(NodeExecutionStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())
