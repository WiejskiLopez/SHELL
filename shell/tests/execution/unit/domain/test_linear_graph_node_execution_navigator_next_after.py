"""Unit tests for LinearGraphNodeExecutionNavigator.next_after."""

from __future__ import annotations

from shell.domain.execution.services.graph_node_execution_navigator import (
    LinearGraphNodeExecutionNavigator,
)
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId

from shell.tests.conftest import _graph_execution, _graph_node_execution


class TestLinearGraphNodeExecutionNavigatorNextAfter:
    def test_next_after_returns_following_node(self) -> None:
        nav = LinearGraphNodeExecutionNavigator()
        graph_execution = _graph_execution(
            _graph_node_execution("a", 0),
            _graph_node_execution("b", 1),
            _graph_node_execution("c", 2),
        )
        nxt = list(nav.next_after(graph_execution, GraphNodeExecutionId("a")))
        assert len(nxt) == 1
        assert nxt[0].id == GraphNodeExecutionId("b")

    def test_next_after_last_node_returns_empty(self) -> None:
        nav = LinearGraphNodeExecutionNavigator()
        graph_execution = _graph_execution(
            _graph_node_execution("a", 0), _graph_node_execution("b", 1)
        )
        assert list(nav.next_after(graph_execution, GraphNodeExecutionId("b"))) == []

    def test_next_after_unknown_node_returns_empty(self) -> None:
        nav = LinearGraphNodeExecutionNavigator()
        graph_execution = _graph_execution(_graph_node_execution("a", 0))
        assert list(nav.next_after(graph_execution, GraphNodeExecutionId("ghost"))) == []

    def test_next_after_respects_position_ordering(self) -> None:
        nav = LinearGraphNodeExecutionNavigator()
        graph_execution = _graph_execution(
            _graph_node_execution("c", 2),
            _graph_node_execution("a", 0),
            _graph_node_execution("b", 1),
        )
        nxt = list(nav.next_after(graph_execution, GraphNodeExecutionId("a")))
        assert nxt and nxt[0].id == GraphNodeExecutionId("b")
        nxt2 = list(nav.next_after(graph_execution, GraphNodeExecutionId("b")))
        assert nxt2 and nxt2[0].id == GraphNodeExecutionId("c")
