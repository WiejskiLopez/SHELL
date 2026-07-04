"""GraphExecutionRoutingService — pure domain routing logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_execution.exceptions.role_not_resolvable import (
    RoleNotResolvable,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.node_execution import (
        NodeExecution,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


class GraphExecutionRoutingService:
    """Resolves target_role -> NodeExecutionId using the task graph."""

    @staticmethod
    def resolve_target_node_execution(
        node_executions: tuple[NodeExecution, ...],
        source_node_execution_id: NodeExecutionId,
        target_role: str | None,
    ) -> NodeExecutionId:
        """Return receiver NodeExecutionId for a given source node and optional target_role.

        Rules:
        1. If target_role is set -> find first non-router node whose role matches.
        2. If target_role is None -> pick first non-router node that is not the source.
        3. If nothing found -> raise RoleNotResolvable.
        """
        non_router = [
            gn for gn in node_executions if node_execution_mode_is_not_router(gn)
        ]

        if target_role:
            matched = [gn for gn in non_router if gn.role == target_role]
            if not matched:
                raise RoleNotResolvable(f"No graph node with role={target_role!r} found")
            return matched[0].id

        candidates = [gn for gn in non_router if gn.id != source_node_execution_id]
        if not candidates and non_router:
            candidates = non_router
        if not candidates:
            raise RoleNotResolvable("Cannot resolve target: no routable nodes")
        return candidates[0].id


def node_execution_mode_is_not_router(gn: NodeExecution) -> bool:
    mode = getattr(gn, "mode", None)
    if mode is not None:
        return str(mode) != "router"
    return True
