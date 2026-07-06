from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
    EdgeLinkExecution,
)
from shell.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


class InMemoryEdgeLinkExecutionRepository(
    InMemoryRepository[EdgeLinkExecution, EdgeLinkExecutionId],
    EdgeLinkExecutionRepository,
):
    async def list_by_node_execution_id(self, node_id: NodeExecutionId) -> list[EdgeLinkExecution]:
        return [copy.deepcopy(e) for e in self._store.values() if e.node_execution_id == node_id]

    async def list_by_edge_execution_id(
        self, edge_execution_id: EdgeExecutionId
    ) -> list[EdgeLinkExecution]:
        return [
            copy.deepcopy(e)
            for e in self._store.values()
            if e.edge_execution_id == edge_execution_id
        ]
