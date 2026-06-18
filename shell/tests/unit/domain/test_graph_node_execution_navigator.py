"""Unit tests for ``LinearGraphNodeExecutionNavigator`` (and the ``NodeNavigator`` Protocol)."""

from __future__ import annotations

from shell.domain.entities.graph_execution import GraphExecution
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.services.graph_node_execution_navigator import LinearGraphNodeExecutionNavigator
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
)
from shell.domain.value_objects.mode import Mode


def _graph_node_execution(
    graph_node_execution_id: str, position: int, mode: str = "agent"
) -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(graph_node_execution_id),
        position=position,
        node_dir=f"/fake/{graph_node_execution_id}",
        mode=Mode(mode),
        role=mode,
        node_type=mode,
    )


def _graph_execution(*graph_node_executions: GraphNodeExecution) -> GraphExecution:
    return GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=TaskExecutionId.generate(),
        graph_definition_id=GraphDefinitionId("tpl"),
        graph_node_executions=list(graph_node_executions),
    )


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
        # Out-of-order list, but ordering must follow ``position``.
        graph_execution = _graph_execution(
            _graph_node_execution("c", 2),
            _graph_node_execution("a", 0),
            _graph_node_execution("b", 1),
        )
        nxt = list(nav.next_after(graph_execution, GraphNodeExecutionId("a")))
        assert nxt and nxt[0].id == GraphNodeExecutionId("b")
        nxt2 = list(nav.next_after(graph_execution, GraphNodeExecutionId("b")))
        assert nxt2 and nxt2[0].id == GraphNodeExecutionId("c")
