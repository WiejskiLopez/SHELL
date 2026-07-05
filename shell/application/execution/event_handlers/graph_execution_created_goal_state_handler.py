"""GraphExecutionCreatedGoalStateHandler — creates initial GraphExecutionState.

Subscribes to GraphExecutionCreatedEvent and creates an empty GraphExecutionState
(direction=IN) so the graph execution has an initial state slot.
Goal data is not carried in the event — consumers fetch it from TaskExecution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
        GraphExecutionCreatedEvent,
    )
    from shell.domain.platform.ports.time import Clock


class GraphExecutionCreatedGoalStateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(
        self, graph_execution_created_event: GraphExecutionCreatedEvent
    ) -> None:
        async with self._unit_of_work as unit_of_work:
            now = self._clock.now()
            state = GraphExecutionState.create(
                id_=GraphExecutionStateId.generate(),
                graph_execution_id=graph_execution_created_event.graph_execution_id,
                direction=StateDirection.IN,
                now=CreatedAt.from_datetime(now),
            )
            await unit_of_work.repository(GraphExecutionStateRepository).save(state)
            unit_of_work.stage_events(state.pull_events())
