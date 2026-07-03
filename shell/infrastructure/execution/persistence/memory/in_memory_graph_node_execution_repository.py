from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (  # noqa: TC002 — GraphNodeExecutionId używany w konstruktorach w repozytorium
    GraphExecutionId,
    GraphNodeExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import (
    InMemoryRepository,
)

if TYPE_CHECKING:
    from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_link_execution_repository import (
        InMemoryGraphNodeLinkExecutionRepository,
    )


class InMemoryGraphNodeExecutionRepository(
    InMemoryRepository[GraphNodeExecution, GraphNodeExecutionId], GraphNodeExecutionRepository
):
    def __init__(self) -> None:
        super().__init__()
        self._link_repo: object = None

    def set_link_repo(self, link_repo: object) -> None:
        self._link_repo = link_repo

    async def list_by_ids(self, ids: list[GraphNodeExecutionId]) -> list[GraphNodeExecution]:
        return [self._store[i.value] for i in ids if i.value in self._store]

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeExecution]:
        if self._link_repo is None:
            return []

        link_repo: InMemoryGraphNodeLinkExecutionRepository = self._link_repo  # type: ignore[assignment]
        links = await link_repo.list_by_graph_execution_id(graph_execution_id)
        result: list[GraphNodeExecution] = []
        for link in links:
            node = self._store.get(link.graph_node_execution_id.value)
            if node is not None:
                result.append(node)
        return result

    async def get_next_pending(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphNodeExecution | None:
        return None
