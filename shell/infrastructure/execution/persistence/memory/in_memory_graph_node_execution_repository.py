from __future__ import annotations

from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (  # noqa: TC002 — GraphNodeExecutionId używany w konstruktorach w repozytorium
    GraphExecutionId,
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.infrastructure.platform.persistence.in_memory_repository import (
    InMemoryRepository,
)


class InMemoryGraphNodeExecutionRepository(InMemoryRepository[GraphNodeExecution, GraphNodeExecutionId], GraphNodeExecutionRepository):

    async def list_by_ids(self, ids: list[GraphNodeExecutionId]) -> list[GraphNodeExecution]:
        return [self._store[i.value] for i in ids if i.value in self._store]

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeExecution]:
        return [
            n
            for n in self._store.values()
            if n.graph_execution_id and n.graph_execution_id == graph_execution_id
        ]

    async def get_next_pending(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphNodeExecution | None:
        return None
