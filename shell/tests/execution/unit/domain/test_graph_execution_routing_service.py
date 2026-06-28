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


def _make_node(node_id: str, position: int, mode: str, role: NodeRole = NodeRole.PLANNER) -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(node_id),
        position=NodeOrder(position),
        mode=Mode(mode),
        role=role,
        node_type=NodeType(mode),
    )


def _make_nodes(*nodes: GraphNodeExecution) -> tuple[GraphNodeExecution, ...]:
    return nodes


class TestResolveTargetGraphNodeExecution:
    def test_resolve_by_role_returns_matching_node(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent", NodeRole("worker")),
            _make_node("b", 2, "tool", NodeRole("calculator")),
            _make_node("c", 3, "router", NodeRole("router")),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), "calculator"
        )
        assert result == GraphNodeExecutionId("b")

    def test_resolve_skips_router_nodes(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "router", NodeRole("router")),
            _make_node("b", 2, "agent", NodeRole("worker")),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("b")

    def test_resolve_without_role_picks_first_other_non_router(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent", NodeRole("x")),
            _make_node("b", 2, "agent", NodeRole("y")),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("b")

    def test_role_not_found_raises(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent", NodeRole("foo")),
        )
        with pytest.raises(RoleNotResolvable, match="role='bar'"):
            GraphExecutionRoutingService.resolve_target_graph_node_execution(
                nodes, GraphNodeExecutionId("a"), "bar"
            )

    def test_all_router_nodes_raises(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "router", NodeRole("r1")),
            _make_node("b", 2, "router", NodeRole("r2")),
        )
        with pytest.raises(RoleNotResolvable, match="no routable nodes"):
            GraphExecutionRoutingService.resolve_target_graph_node_execution(
                nodes, GraphNodeExecutionId("a"), None
            )

    def test_single_non_router_node_falls_back_to_itself(self) -> None:
        nodes = _make_nodes(
            _make_node("a", 1, "agent", NodeRole("x")),
        )
        result = GraphExecutionRoutingService.resolve_target_graph_node_execution(
            nodes, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("a")
