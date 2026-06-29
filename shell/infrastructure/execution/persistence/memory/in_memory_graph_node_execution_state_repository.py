from __future__ import annotations

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
    GraphNodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
    GraphNodeExecutionStateId,
)
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.execution.aggregates.graph_node_execution_state.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryGraphNodeExecutionStateRepository(InMemoryRepository[GraphNodeExecutionState, GraphNodeExecutionStateId], GraphNodeExecutionStateRepository):

    def __init__(self) -> None:
        self._store: dict[str, list[GraphNodeExecutionState]] = {}  # type: ignore[assignment]

    async def get_by_id(self, id_: GraphNodeExecutionStateId) -> GraphNodeExecutionState | None:
        for states in self._store.values():
            for state in states:
                if state.id == id_:
                    return state
        return None

    async def list_by_graph_node_execution_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> list[GraphNodeExecutionState]:
        return self._store.get(graph_node_execution_id.value, [])

    async def list_by_graph_node_execution_and_direction(
        self, graph_node_execution_id: GraphNodeExecutionId, direction: StateDirection
    ) -> list[GraphNodeExecutionState]:
        return [s for s in self._store.get(graph_node_execution_id.value, []) if s.direction == direction]

    async def save(self, state: GraphNodeExecutionState) -> None:
        key = state.graph_node_execution_id.value
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(state)

    async def delete(self, id_: GraphNodeExecutionStateId) -> None:
        for states in self._store.values():
            for i, state in enumerate(states):
                if state.id == id_:
                    states.pop(i)
                    return

    async def exists(self, id_: GraphNodeExecutionStateId) -> ExistsResult:
        for states in self._store.values():
            for state in states:
                if state.id == id_:
                    return ExistsResult(True)
        return ExistsResult(False)
