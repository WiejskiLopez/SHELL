from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.edge_execution.edge_execution import (
    EdgeExecution,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


class InMemoryEdgeExecutionRepository(
    InMemoryRepository[EdgeExecution, EdgeExecutionId],
    EdgeExecutionRepository,
):
    async def list_by_source_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]:
        return [
            copy.deepcopy(e) for e in self._store.values() if e.source_node_execution_id == node_id
        ]

    async def list_by_target_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]:
        return [
            copy.deepcopy(e) for e in self._store.values() if e.target_node_execution_id == node_id
        ]
