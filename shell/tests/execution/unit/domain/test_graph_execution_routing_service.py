from __future__ import annotations

import pytest
from shell.domain.definition.value_objects.ids import GraphDefinitionId
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.exceptions import RoleNotResolvable
from shell.domain.execution.services.graph_execution_routing_service import (
    GraphExcetutionRoutingService,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
)
from shell.domain.platform.value_objects.mode import Mode


def _make_node(node_id: str, position: int, mode: str, role: str = "") -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(node_id),
        position=position,
        mode=Mode(mode),
        role=role or mode,
        node_type=mode,
    )


def _make_graph_execution(*nodes: GraphNodeExecution) -> GraphExecution:
    return GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=TaskExecutionId("t1"),
        graph_definition_id=GraphDefinitionId("g1"),
        graph_node_executions=list(nodes),
    )


class TestResolveTargetGraphNodeExecution:
    def test_resolve_by_role_returns_matching_node(self) -> None:
        ge = _make_graph_execution(
            _make_node("a", 1, "agent", "worker"),
            _make_node("b", 2, "tool", "calculator"),
            _make_node("c", 3, "router", "router"),
        )
        result = GraphExcetutionRoutingService.resolve_target_graph_node_execution(
            ge, GraphNodeExecutionId("a"), "calculator"
        )
        assert result == GraphNodeExecutionId("b")

    def test_resolve_skips_router_nodes(self) -> None:
        ge = _make_graph_execution(
            _make_node("a", 1, "router", "router"),
            _make_node("b", 2, "agent", "worker"),
        )
        result = GraphExcetutionRoutingService.resolve_target_graph_node_execution(
            ge, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("b")

    def test_resolve_without_role_picks_first_other_non_router(self) -> None:
        ge = _make_graph_execution(
            _make_node("a", 1, "agent", "x"),
            _make_node("b", 2, "agent", "y"),
        )
        result = GraphExcetutionRoutingService.resolve_target_graph_node_execution(
            ge, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("b")

    def test_role_not_found_raises(self) -> None:
        ge = _make_graph_execution(
            _make_node("a", 1, "agent", "foo"),
        )
        with pytest.raises(RoleNotResolvable, match="role='bar'"):
            GraphExcetutionRoutingService.resolve_target_graph_node_execution(
                ge, GraphNodeExecutionId("a"), "bar"
            )

    def test_all_router_nodes_raises(self) -> None:
        ge = _make_graph_execution(
            _make_node("a", 1, "router", "r1"),
            _make_node("b", 2, "router", "r2"),
        )
        with pytest.raises(RoleNotResolvable, match="no routable nodes"):
            GraphExcetutionRoutingService.resolve_target_graph_node_execution(
                ge, GraphNodeExecutionId("a"), None
            )

    def test_single_non_router_node_falls_back_to_itself(self) -> None:
        ge = _make_graph_execution(
            _make_node("a", 1, "agent", "x"),
        )
        result = GraphExcetutionRoutingService.resolve_target_graph_node_execution(
            ge, GraphNodeExecutionId("a"), None
        )
        assert result == GraphNodeExecutionId("a")
