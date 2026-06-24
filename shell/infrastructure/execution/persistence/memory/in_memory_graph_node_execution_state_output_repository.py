from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_state_output_repository import (
    GraphNodeExecutionStateOutputRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,  # noqa: TC002 — GraphNodeExecutionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
        GraphNodeExecutionStateOutput,
    )


class InMemoryGraphNodeExecutionStateOutputRepository(GraphNodeExecutionStateOutputRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeExecutionStateOutput] = {}

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionStateOutput | None:
        for payload in self._store.values():
            if payload.graph_node_execution_id == graph_node_execution_id and payload.is_current:
                return payload
        return None

    async def save(self, payload: GraphNodeExecutionStateOutput) -> None:
        self._store[payload.id.value] = payload
