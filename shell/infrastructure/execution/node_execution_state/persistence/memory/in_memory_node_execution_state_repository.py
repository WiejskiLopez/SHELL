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
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.platform.value_objects.state_direction import StateDirection


class InMemoryNodeExecutionStateRepository(
    InMemoryRepository[NodeExecutionState, NodeExecutionStateId],
    NodeExecutionStateRepository,
):
    def __init__(self) -> None:
        self._store: dict[str, list[NodeExecutionState]] = {}  # type: ignore[assignment]

    async def get_by_id(self, id_: NodeExecutionStateId) -> NodeExecutionState | None:
        for states in self._store.values():
            for state in states:
                if state.id == id_:
                    return state
        return None

    async def list_by_node_execution_id(
        self, node_execution_id: NodeExecutionId
    ) -> list[NodeExecutionState]:
        return self._store.get(node_execution_id.value, [])

    async def list_by_node_execution_and_direction(
        self, node_execution_id: NodeExecutionId, direction: StateDirection
    ) -> list[NodeExecutionState]:
        return [s for s in self._store.get(node_execution_id.value, []) if s.direction == direction]

    async def save(self, state: NodeExecutionState) -> None:
        key = state.node_execution_id.value
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(state)

    async def delete(self, id_: NodeExecutionStateId, now: datetime | None = None) -> None:
        for states in self._store.values():
            for i, state in enumerate(states):
                if state.id == id_:
                    states.pop(i)
                    return

    async def exists(self, id_: NodeExecutionStateId) -> ExistsResult:
        for states in self._store.values():
            for state in states:
                if state.id == id_:
                    return ExistsResult(True)
        return ExistsResult(False)
