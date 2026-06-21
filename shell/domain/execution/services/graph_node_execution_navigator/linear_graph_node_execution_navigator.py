from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import GraphNodeExecution
    from shell.domain.execution.aggregates.graph_node_execution.ports.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId


class LinearGraphNodeExecutionNavigator:

    @staticmethod
    def first(graph_execution: GraphExecution) -> GraphNodeExecution | None:
        ordered = sorted(graph_execution.graph_node_executions, key=lambda n: n.position)
        return ordered[0] if ordered else None

    @staticmethod
    def next_after(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> list[GraphNodeExecution]:
        ordered = sorted(graph_execution.graph_node_executions, key=lambda n: n.position)
        for idx, node in enumerate(ordered):
            if node.id == graph_node_execution_id:
                return [ordered[idx + 1]] if idx + 1 < len(ordered) else []
        return []

    @staticmethod
    async def first_async(
        graph_execution: GraphExecution,
        node_repo: GraphNodeExecutionRepository,
    ) -> GraphNodeExecution | None:
        node_ids = list(graph_execution.graph_node_execution_ids)
        if not node_ids:
            return None
        nodes = await node_repo.list_by_ids(node_ids)
        ordered = sorted(nodes, key=lambda n: n.position)
        return ordered[0] if ordered else None

    @staticmethod
    async def next_after_async(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        node_repo: GraphNodeExecutionRepository,
    ) -> list[GraphNodeExecution]:
        node_ids = list(graph_execution.graph_node_execution_ids)
        if not node_ids:
            return []
        nodes = await node_repo.list_by_ids(node_ids)
        ordered = sorted(nodes, key=lambda n: n.position)
        for idx, node in enumerate(ordered):
            if node.id == graph_node_execution_id:
                return [ordered[idx + 1]] if idx + 1 < len(ordered) else []
        return []
