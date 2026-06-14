"""GraphRoutingService — pure domain routing logic."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.exceptions import RoleNotResolvable

if TYPE_CHECKING:
    from shell_ddd.domain.entities.graph import Graph
    from shell_ddd.domain.entities.graph_node import GraphNode
    from shell_ddd.domain.value_objects.ids import NodeId


class GraphRoutingService:
    """Resolves target_role -> NodeId using the task graph."""

    @staticmethod
    def resolve_target_node(
        graph: Graph,
        source_node_id: NodeId,
        target_role: str | None,
    ) -> NodeId:
        """Return receiver NodeId for a given source node and optional target_role.

        Rules (matching legacy _run_router):
        1. If target_role is set → find first non-router node whose role matches.
        2. If target_role is None → pick first non-router node that is not the source.
        3. If nothing found → raise RoleNotResolvable.
        """
        non_router: list[GraphNode] = [
            n for n in graph.nodes if str(n.mode) != "router"
        ]

        if target_role:
            matched = [n for n in non_router if n.role == target_role]
            if not matched:
                raise RoleNotResolvable(
                    f"No graph node with role={target_role!r} found in graph {graph.id}"
                )
            return matched[0].id

        candidates = [n for n in non_router if n.id != source_node_id]
        if not candidates and non_router:
            candidates = non_router  # fallback: send to first non-router even if same
        if not candidates:
            raise RoleNotResolvable(
                f"Cannot resolve target: graph {graph.id} has no routable nodes"
            )
        return candidates[0].id
