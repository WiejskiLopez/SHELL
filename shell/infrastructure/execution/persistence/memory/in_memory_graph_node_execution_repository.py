from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution


class InMemoryGraphNodeExecutionRepository(GraphNodeExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeExecution] = {}

    async def get_by_id(self, node_id: GraphNodeExecutionId) -> GraphNodeExecution | None:
        return self._store.get(node_id.value)

    async def save(self, node: GraphNodeExecution) -> None:
        self._store[node.id.value] = node

    async def list_by_ids(self, ids: list[GraphNodeExecutionId]) -> list[GraphNodeExecution]:
        return [self._store[i.value] for i in ids if i.value in self._store]

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeExecution]:
        return [
            n for n in self._store.values()
            if n.graph_execution_id and n.graph_execution_id == graph_execution_id
        ]
