"""NodeNavigator — domain service deciding which node runs next in a Graph.

Implementations encapsulate the **ordering policy**: linear, branching, parallel,
conditional. The default ``LinearGraphNodeExecutionNavigator`` orders nodes by ``GraphNode.position``.

The navigator is a *pure* domain service — no I/O, no async — and lives in
``domain/services/`` because it expresses business behaviour (graph traversal).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.entities.graph_execution import GraphExecution
    from shell.domain.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class NodeNavigator(Protocol):
    """Decides the next node(s) to execute in a Graph."""

    def first(self, graph_execution: GraphExecution) -> GraphNodeExecution | None:
        """Return the first node to execute, or None if the graph has no nodes."""
        ...

    def next_after(
        self, graph_execution: GraphExecution, graph_node_execution_id: GraphNodeExecutionId
    ) -> Iterable[GraphNodeExecution]:
        """Return the node(s) that should follow ``node_execution_id`` in execution order.

        Returning an empty iterable signals that no further node remains and the
        workflow has reached a terminal state. The contract intentionally returns
        an Iterable (not a single node) so that future implementations can fan out
        into multiple parallel nodes without changing the worker.
        """
        ...


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
