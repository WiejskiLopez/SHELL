from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


class InMemoryNodeLinkExecutionRepository(
    InMemoryRepository[NodeLinkExecution, NodeLinkExecutionId],
):
    async def get_by_id(
        self,
        node_link_execution_id: NodeLinkExecutionId,
    ) -> NodeLinkExecution | None:
        return self._store.get(node_link_execution_id.value)

    async def list_by_graph_execution_id(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> list[NodeLinkExecution]:
        return [
            link for link in self._store.values() if link.graph_execution_id == graph_execution_id
        ]

    async def list_by_node_execution_id(
        self,
        node_execution_id: NodeExecutionId,
    ) -> list[NodeLinkExecution]:
        return [
            link for link in self._store.values() if link.node_execution_id == node_execution_id
        ]

    async def save(self, link: NodeLinkExecution) -> None:
        self._store[link.id.value] = link

    async def delete(self, id: NodeLinkExecutionId, now: datetime | None = None) -> None:
        self._store.pop(id.value, None)

    async def exists(self, id: NodeLinkExecutionId) -> ExistsResult:
        return ExistsResult(id.value in self._store)
