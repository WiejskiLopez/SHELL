"""Unit tests for LinearGraphNodeExecutionNavigator.first."""

from __future__ import annotations

from shell.domain.execution.services.graph_node_execution_navigator import (
    LinearGraphNodeExecutionNavigator,
)
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId

from tests.conftest import _graph_execution, _graph_node_execution


class TestLinearGraphNodeExecutionNavigatorFirst:
    def test_first_returns_lowest_position(self) -> None:
        nav = LinearGraphNodeExecutionNavigator()
        graph_execution = _graph_execution(
            _graph_node_execution("b", 1),
            _graph_node_execution("a", 0),
            _graph_node_execution("c", 2),
        )
        result = nav.first(graph_execution)
        assert result is not None
        assert result.id == GraphNodeExecutionId("a")

    def test_first_on_empty_graph_returns_none(self) -> None:
        nav = LinearGraphNodeExecutionNavigator()
        graph_execution = _graph_execution()
        assert nav.first(graph_execution) is None

    def test_first_handles_unsorted_input(self) -> None:
        nav = LinearGraphNodeExecutionNavigator()
        graph_execution = _graph_execution(
            _graph_node_execution("z", 5),
            _graph_node_execution("y", 3),
            _graph_node_execution("x", 1),
        )
        first = nav.first(graph_execution)
        assert first is not None
        assert first.id == GraphNodeExecutionId("x")
