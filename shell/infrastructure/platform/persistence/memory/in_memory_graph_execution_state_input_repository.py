from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )


class InMemoryGraphExecutionStateRepository(GraphExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, list[GraphExecutionState]] = {}

    async def get_current_by_graph_execution_id_and_direction(
        self, graph_execution_id: GraphExecutionId, direction: StateDirection
    ) -> GraphExecutionState | None:
        versions = self._store.get(graph_execution_id.value, [])
        for state in reversed(versions):
            if state.is_current.value and state.direction == direction:
                return state
        return None

    async def save(self, state: GraphExecutionState) -> None:
        if state.graph_execution_id.value not in self._store:
            self._store[state.graph_execution_id.value] = []
        if state.is_current.value:
            for existing in self._store[state.graph_execution_id.value]:
                existing.supersede()
        self._store[state.graph_execution_id.value].append(state)

    async def delete(self, id: object) -> None:
        ...

    async def exists(self, id: object) -> bool:
        ...
