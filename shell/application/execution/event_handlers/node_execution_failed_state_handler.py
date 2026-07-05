"""NodeExecutionFailedStateHandler — creates state on node failure.

Subscribes to NodeExecutionFailedEvent. Creates a NodeExecutionState
(direction=OUT) with the error payload. Modyfikuje tylko NodeExecutionState.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    from shell.domain.execution.aggregates.node_execution.events.node_execution_failed_event import (
        NodeExecutionFailedEvent,
    )
    from shell.domain.platform.ports.time import Clock


class NodeExecutionFailedStateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(
        self, event: NodeExecutionFailedEvent
    ) -> None:
        now = self._clock.now()
        async with self._unit_of_work as unit_of_work:
            payload: dict[str, object] = {
                "status": "failed",
            }

            state = NodeExecutionState.create(
                id_=NodeExecutionStateId.generate(),
                node_execution_id=event.node_id,
                direction=StateDirection.OUT,
                payload=payload,
                now=now,
            )
            await unit_of_work.repository(NodeExecutionStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())
