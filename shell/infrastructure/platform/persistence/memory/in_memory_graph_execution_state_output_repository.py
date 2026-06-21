from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution_state_output.ports.graph_execution_state_output_repository import (
    GraphExecutionStateOutputRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state_output.graph_execution_state_output import (
        GraphExecutionStateOutput,
    )


class InMemoryGraphExecutionStateOutputRepository(GraphExecutionStateOutputRepository):
    def __init__(self) -> None:
        self._store: dict[str, list[GraphExecutionStateOutput]] = {}

    async def get_current_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphExecutionStateOutput | None:
        versions = self._store.get(graph_execution_id.value, [])
        for state in reversed(versions):
            if state.is_current:
                return state
        return None

    async def save(self, state: GraphExecutionStateOutput) -> None:
        if state.graph_execution_id.value not in self._store:
            self._store[state.graph_execution_id.value] = []
        if state.is_current:
            for existing in self._store[state.graph_execution_id.value]:
                existing.supersede()
        self._store[state.graph_execution_id.value].append(state)
