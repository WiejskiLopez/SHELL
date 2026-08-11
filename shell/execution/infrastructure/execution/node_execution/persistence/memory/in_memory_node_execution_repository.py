from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.execution.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import (
    InMemoryRepository,
)

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.execution.infrastructure.execution.node_link_execution.persistence.memory.in_memory_node_link_execution_repository import (
        InMemoryNodeLinkExecutionRepository,
    )


class InMemoryNodeExecutionRepository(
    InMemoryRepository[NodeExecution, NodeExecutionId], NodeExecutionRepository
):
    def __init__(self) -> None:
        super().__init__()
        self._link_repo: object = None

    def set_link_repository(self, link_repo: object) -> None:
        self._link_repo = link_repo

    async def list_by_ids(self, ids: list[NodeExecutionId]) -> list[NodeExecution]:
        return [self._store[i.value] for i in ids if i.value in self._store]

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[NodeExecution]:
        if self._link_repo is None:
            return []

        link_repo: InMemoryNodeLinkExecutionRepository = self._link_repo  # type: ignore[assignment]
        links = await link_repo.list_by_graph_execution_id(graph_execution_id)
        result: list[NodeExecution] = []
        for link in links:
            node = self._store.get(link.node_execution_id.value)
            if node is not None:
                result.append(node)
        return result

    async def get_next_pending(self, graph_execution_id: GraphExecutionId) -> NodeExecution | None:
        return None
