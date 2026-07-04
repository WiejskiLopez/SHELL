from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_transition_execution.node_transition_execution import (
    NodeTransitionExecution,
)
from shell.domain.execution.aggregates.node_transition_execution.repositories.node_transition_execution_repository import (
    NodeTransitionExecutionRepository,
)
from shell.domain.execution.aggregates.node_transition_execution.value_objects.node_transition_execution_id import (
    NodeTransitionExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
    )


class InMemoryNodeTransitionExecutionRepository(  # type: ignore[misc]
    InMemoryRepository[NodeTransitionExecution, NodeTransitionExecutionId],
    NodeTransitionExecutionRepository,
):
    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[NodeTransitionExecution]:
        return [
            copy.deepcopy(t)
            for t in self._store.values()
            if t.graph_execution_id == graph_execution_id
        ]

    async def list_outgoing_for_node(
        self, node_id: NodeExecutionId
    ) -> list[NodeTransitionExecution]:
        return [
            copy.deepcopy(t) for t in self._store.values() if t.source_node_execution_id == node_id
        ]
