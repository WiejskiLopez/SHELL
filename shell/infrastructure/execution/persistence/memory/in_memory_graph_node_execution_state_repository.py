from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
    GraphNodeExecutionStateRepository,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution_state.graph_node_execution_state import (
        GraphNodeExecutionState,
    )


class InMemoryGraphNodeExecutionStateRepository(GraphNodeExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, list[GraphNodeExecutionState]] = {}

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

    async def delete(self, id_: object) -> None:
        ...

    async def exists(self, id_: object) -> bool:
        return False
