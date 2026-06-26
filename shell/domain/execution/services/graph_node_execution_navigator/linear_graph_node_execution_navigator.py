from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.graph_node_transition_execution.repositories.graph_node_transition_execution_repository import (
        GraphNodeTransitionExecutionRepository,
    )


class LinearGraphNodeExecutionNavigator:
    @staticmethod
    async def first_async(
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> GraphNodeExecution | None:
        nodes = await node_repo.list_by_graph_execution_id(graph_execution.id)
        if not nodes:
            return None
        ordered = sorted(nodes, key=lambda n: n.position)
        return ordered[0] if ordered else None

    @staticmethod
    async def next_after_async(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
        transition_repo: GraphNodeTransitionExecutionRepository,
    ) -> Iterable[GraphNodeExecution]:
        nodes = await node_repo.list_by_graph_execution_id(graph_execution.id)
        if not nodes:
            return []
        ordered = sorted(nodes, key=lambda n: n.position)
        for idx, node in enumerate(ordered):
            if node.id == graph_node_execution_id:
                return [ordered[idx + 1]] if idx + 1 < len(ordered) else []
        return []
