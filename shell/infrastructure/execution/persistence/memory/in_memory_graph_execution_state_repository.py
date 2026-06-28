from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )


class InMemoryGraphExecutionStateRepository(GraphExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphExecutionState] = {}

    async def get_current_by_graph_execution_id_and_direction(
        self, graph_execution_id: GraphExecutionId, direction: StateDirection
    ) -> GraphExecutionState | None:
        for item in self._store.values():
            if item.graph_execution_id == graph_execution_id and item.direction == direction:
                return copy.deepcopy(item)
        return None

    async def save(self, state: GraphExecutionState) -> None:
        self._store[state.id.value] = copy.deepcopy(state)

    async def delete(self, id: object) -> None:
        key = str(id)
        self._store.pop(key, None)

    async def exists(self, id: object) -> bool:
        return str(id) in self._store
