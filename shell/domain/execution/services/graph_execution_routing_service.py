"""GraphExcetutionRoutingService — pure domain routing logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.exceptions.role_not_resolvable import (
    RoleNotResolvable,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
        GraphNodeExecutionId,
    )


class GraphExcetutionRoutingService:
    """Resolves target_role -> GraphNodeExecutionId using the task graph."""

    @staticmethod
    def resolve_target_graph_node_execution(
        graph_execution: GraphExecution,
        source_node_execution_id: GraphNodeExecutionId,
        target_role: str | None,
    ) -> GraphNodeExecutionId:
        """Return receiver GraphNodeExecutionId for a given source node and optional target_role.

        Rules (matching legacy _run_router):
        1. If target_role is set → find first non-router node whose role matches.
        2. If target_role is None → pick first non-router node that is not the source.
        3. If nothing found → raise RoleNotResolvable.
        """
        non_router: list[GraphNodeExecution] = [
            graph_node_execution
            for graph_node_execution in graph_execution.graph_node_executions
            if str(graph_node_execution.mode) != "router"
        ]

        if target_role:
            matched = [
                graph_node_execution
                for graph_node_execution in non_router
                if graph_node_execution.role == target_role
            ]
            if not matched:
                raise RoleNotResolvable(
                    f"No graph node with role={target_role!r} found in graph_execution {graph_execution.id}"
                )
            return matched[0].id

        candidates = [
            graph_node_execution
            for graph_node_execution in non_router
            if graph_node_execution.id != source_node_execution_id
        ]
        if not candidates and non_router:
            candidates = non_router  # fallback: send to first non-router even if same
        if not candidates:
            raise RoleNotResolvable(
                f"Cannot resolve target: graph_execution {graph_execution.id} has no routable nodes"
            )
        return candidates[0].id
