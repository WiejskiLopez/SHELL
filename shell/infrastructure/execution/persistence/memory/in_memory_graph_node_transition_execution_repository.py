from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_transition_execution.graph_node_transition_execution import (
    GraphNodeTransitionExecution,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.repositories.graph_node_transition_execution_repository import (
    GraphNodeTransitionExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
    )


class InMemoryGraphNodeTransitionExecutionRepository(  # type: ignore[misc]
    InMemoryRepository[GraphNodeTransitionExecution, GraphNodeTransitionExecutionId],
    GraphNodeTransitionExecutionRepository,
):
    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeTransitionExecution]:
        return [
            copy.deepcopy(t)
            for t in self._store.values()
            if t.graph_execution_id == graph_execution_id
        ]

    async def list_outgoing_for_node(
        self, node_id: GraphNodeExecutionId
    ) -> list[GraphNodeTransitionExecution]:
        return [
            copy.deepcopy(t) for t in self._store.values() if t.source_node_execution_id == node_id
        ]
