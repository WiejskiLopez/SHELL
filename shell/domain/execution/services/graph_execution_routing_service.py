"""GraphExecutionRoutingService — pure domain routing logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.exceptions.role_not_resolvable import (
    RoleNotResolvable,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )


class GraphExecutionRoutingService:
    """Resolves target_role -> GraphNodeExecutionId using the task graph."""

    @staticmethod
    def resolve_target_graph_node_execution(
        graph_node_executions: tuple[GraphNodeExecution, ...],
        source_node_execution_id: GraphNodeExecutionId,
        target_role: str | None,
    ) -> GraphNodeExecutionId:
        """Return receiver GraphNodeExecutionId for a given source node and optional target_role.

        Rules:
        1. If target_role is set -> find first non-router node whose role matches.
        2. If target_role is None -> pick first non-router node that is not the source.
        3. If nothing found -> raise RoleNotResolvable.
        """
        non_router = [
            gn for gn in graph_node_executions
            if graph_node_execution_mode_is_not_router(gn)
        ]

        if target_role:
            matched = [
                gn for gn in non_router if gn.role == target_role
            ]
            if not matched:
                raise RoleNotResolvable(
                    f"No graph node with role={target_role!r} found"
                )
            return matched[0].id

        candidates = [
            gn for gn in non_router
            if gn.id != source_node_execution_id
        ]
        if not candidates and non_router:
            candidates = non_router
        if not candidates:
            raise RoleNotResolvable(
                f"Cannot resolve target: no routable nodes"
            )
        return candidates[0].id


def graph_node_execution_mode_is_not_router(gn: GraphNodeExecution) -> bool:
    mode = getattr(gn, "mode", None)
    if mode is not None:
        return str(mode) != "router"
    return True
