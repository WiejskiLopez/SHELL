from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_link_execution.graph_node_link_execution import (
    GraphNodeLinkExecution,
)
from shell.domain.execution.aggregates.graph_node_link_execution.value_objects.graph_node_link_execution_id import (
    GraphNodeLinkExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class InMemoryGraphNodeLinkExecutionRepository(
    InMemoryRepository[GraphNodeLinkExecution, GraphNodeLinkExecutionId],
):
    async def get_by_id(
        self,
        graph_node_link_execution_id: GraphNodeLinkExecutionId,
    ) -> GraphNodeLinkExecution | None:
        return self._store.get(graph_node_link_execution_id.value)

    async def list_by_graph_execution_id(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> list[GraphNodeLinkExecution]:
        return [
            link
            for link in self._store.values()
            if link.graph_execution_id == graph_execution_id
        ]

    async def list_by_graph_node_execution_id(
        self,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> list[GraphNodeLinkExecution]:
        return [
            link
            for link in self._store.values()
            if link.graph_node_execution_id == graph_node_execution_id
        ]

    async def save(self, link: GraphNodeLinkExecution) -> None:
        self._store[link.id.value] = link

    async def delete(self, id: GraphNodeLinkExecutionId) -> None:
        self._store.pop(id.value, None)

    async def exists(self, id: GraphNodeLinkExecutionId) -> ExistsResult:
        return ExistsResult(id.value in self._store)
