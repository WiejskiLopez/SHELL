from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)
from shell.domain.execution.aggregates.graph_node_transition_execution.repositories.graph_node_transition_execution_repository import (
    GraphNodeTransitionExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_transition_execution.graph_node_transition_execution import (
        GraphNodeTransitionExecution,
    )


class InMemoryGraphNodeTransitionExecutionRepository(GraphNodeTransitionExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeTransitionExecution] = {}

    async def get_by_id(
        self, id_: GraphNodeTransitionExecutionId
    ) -> GraphNodeTransitionExecution | None:
        item = self._store.get(id_.value)
        return copy.deepcopy(item) if item is not None else None

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
            copy.deepcopy(t)
            for t in self._store.values()
            if t.source_node_execution_id == node_id
        ]

    async def save(
        self, transition: GraphNodeTransitionExecution
    ) -> None:
        self._store[transition.id.value] = copy.deepcopy(transition)
