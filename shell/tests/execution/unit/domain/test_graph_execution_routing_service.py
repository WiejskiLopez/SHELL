from __future__ import annotations

import pytest

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.exceptions import RoleNotResolvable
from shell.domain.execution.services.graph_execution_routing_service import (
    GraphExecutionRoutingService,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.platform.value_objects.mode import Mode


def _make_node(
    node_id: str, position: int, mode: str, role: str | None = None
) -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(node_id),
        position=NodeOrder(position),
        mode=Mode(mode),
        role=NodeRole(role.upper()) if role else NodeRole.PLANNER,
        node_type=NodeType(mode),
    )


def _make_nodes(*nodes: GraphNodeExecution) -> tuple[GraphNodeExecution, ...]:
    return nodes


class TestResolveTargetGraphNodeExecution:
    def test_resolve_by_role_returns_matching_node(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent", "agent"),
            _make_node("b", 2, "tool", "tool"),
            _make_node("c", 3, "router", "verifier"),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), "TOOL"
        )
        assert result == GraphNodeExecutionId("b")

    def test_resolve_skips_router_nodes(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "router", "verifier"),
            _make_node("b", 2, "agent", "agent"),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("b")

    def test_resolve_without_role_picks_first_other_non_router(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent"),
            _make_node("b", 2, "agent"),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("b")

    def test_role_not_found_raises(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent", "agent"),
        )
        with pytest.raises(RoleNotResolvable, match="role='VERIFIER'"):
            GraphExecutionRoutingService.resolve_target_graph_node_execution(
                nodes, GraphNodeExecutionId("a"), "VERIFIER"
            )

    def test_all_router_nodes_raises(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "router"),
            _make_node("b", 2, "router"),
        )
        with pytest.raises(RoleNotResolvable, match="no routable nodes"):
            GraphExecutionRoutingService.resolve_target_graph_node_execution(
                nodes, GraphNodeExecutionId("a"), None
            )

    def test_single_non_router_node_falls_back_to_itself(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent"),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("a")
