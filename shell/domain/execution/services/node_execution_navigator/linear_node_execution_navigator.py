from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.node_execution.node_execution import (
        NodeExecution,
    )
    from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
        NodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.node_transition_execution.repositories.node_transition_execution_repository import (
        NodeTransitionExecutionRepository,
    )


class LinearNodeExecutionNavigator:
    @staticmethod
    async def first_async(
        graph_execution: GraphExecution,
        node_repo: NodeExecutionRepository,
        transition_repo: NodeTransitionExecutionRepository,
    ) -> NodeExecution | None:
        nodes = await node_repo.list_by_graph_execution_id(graph_execution.id)
        if not nodes:
            return None
        ordered = sorted(nodes, key=lambda n: n.position.value)
        return ordered[0] if ordered else None

    @staticmethod
    async def next_after_async(
        graph_execution: GraphExecution,
        node_execution_id: NodeExecutionId,
        node_repo: NodeExecutionRepository,
        transition_repo: NodeTransitionExecutionRepository,
    ) -> Iterable[NodeExecution]:
        nodes = await node_repo.list_by_graph_execution_id(graph_execution.id)
        if not nodes:
            return []
        ordered = sorted(nodes, key=lambda n: n.position.value)
        for idx, node in enumerate(ordered):
            if node.id == node_execution_id:
                return [ordered[idx + 1]] if idx + 1 < len(ordered) else []
        return []
