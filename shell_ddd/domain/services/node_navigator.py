"""NodeNavigator — domain service deciding which node runs next in a Graph.

Implementations encapsulate the **ordering policy**: linear, branching, parallel,
conditional. The default ``LinearNodeNavigator`` orders nodes by ``GraphNode.position``.

The navigator is a *pure* domain service — no I/O, no async — and lives in
``domain/services/`` because it expresses business behaviour (graph traversal).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.graph import Graph
    from shell_ddd.domain.entities.graph_node import GraphNode
    from shell_ddd.domain.value_objects.ids import NodeId


class NodeNavigator(Protocol):
    """Decides the next node(s) to execute in a Graph."""

    def first(self, graph: "Graph") -> "GraphNode | None":
        """Return the first node to execute, or None if the graph has no nodes."""
        ...

    def next_after(self, graph: "Graph", node_id: "NodeId") -> Iterable["GraphNode"]:
        """Return the node(s) that should follow ``node_id`` in execution order.

        Returning an empty iterable signals that no further node remains and the
        workflow has reached a terminal state. The contract intentionally returns
        an Iterable (not a single node) so that future implementations can fan out
        into multiple parallel nodes without changing the worker.
        """
        ...


class LinearNodeNavigator:
    """Default implementation: orders nodes by ``GraphNode.position`` ascending.

    Falls back to the original list order for nodes sharing the same position.
    """

    def first(self, graph: "Graph") -> "GraphNode | None":
        ordered = self._ordered(graph)
        return ordered[0] if ordered else None

    def next_after(self, graph: "Graph", node_id: "NodeId") -> list["GraphNode"]:
        ordered = self._ordered(graph)
        for idx, node in enumerate(ordered):
            if node.id == node_id:
                return [ordered[idx + 1]] if idx + 1 < len(ordered) else []
        return []

    @staticmethod
    def _ordered(graph: "Graph") -> list["GraphNode"]:
        return sorted(graph.nodes, key=lambda n: n.position)
