from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.execution.value_objects.ids import GraphNodeExecutionId


class LinearGraphNodeExecutionNavigator:
    """Default implementation: orders nodes by ``GraphNode.position`` ascending.

    Falls back to the original list order for nodes sharing the same position.
    """

    def first(self, graph_execution: GraphExecution) -> GraphNodeExecution | None:
        ordered = self._ordered(graph_execution)
        return ordered[0] if ordered else None

    def next_after(
        self, graph_execution: GraphExecution, graph_node_execution_id: GraphNodeExecutionId
    ) -> list[GraphNodeExecution]:
        ordered = self._ordered(graph_execution)
        for idx, node in enumerate(ordered):
            if node.id == graph_node_execution_id:
                return [ordered[idx + 1]] if idx + 1 < len(ordered) else []
        return []

    @staticmethod
    def _ordered(graph_execution: GraphExecution) -> list[GraphNodeExecution]:
        return sorted(graph_execution.graph_node_executions, key=lambda n: n.position)
