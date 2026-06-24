from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution_state_input.repositories.graph_execution_state_input_repository import (
    GraphExecutionStateInputRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state_input.graph_execution_state_input import (
        GraphExecutionStateInput,
    )


class InMemoryGraphExecutionStateInputRepository(GraphExecutionStateInputRepository):
    def __init__(self) -> None:
        self._store: dict[str, list[GraphExecutionStateInput]] = {}

    async def get_current_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphExecutionStateInput | None:
        versions = self._store.get(graph_execution_id.value, [])
        for state in reversed(versions):
            if state.is_current:
                return state
        return None

    async def save(self, state: GraphExecutionStateInput) -> None:
        if state.graph_execution_id.value not in self._store:
            self._store[state.graph_execution_id.value] = []
        if state.is_current:
            for existing in self._store[state.graph_execution_id.value]:
                existing.supersede()
        self._store[state.graph_execution_id.value].append(state)
