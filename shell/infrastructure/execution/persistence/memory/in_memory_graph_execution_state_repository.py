from __future__ import annotations

import copy

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryGraphExecutionStateRepository(InMemoryRepository[GraphExecutionState, GraphExecutionStateId], GraphExecutionStateRepository):

    async def get_current_by_graph_execution_id_and_direction(
        self, graph_execution_id: GraphExecutionId, direction: StateDirection
    ) -> GraphExecutionState | None:
        for item in self._store.values():
            if item.graph_execution_id == graph_execution_id and item.direction == direction:
                return copy.deepcopy(item)
        return None

    async def save(self, state: GraphExecutionState) -> None:
        self._store[state.id.value] = copy.deepcopy(state)

    async def exists(self, id: object) -> ExistsResult:
        return ExistsResult(str(id) in self._store)
