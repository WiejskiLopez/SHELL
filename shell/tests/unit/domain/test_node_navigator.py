"""Unit tests for ``LinearNodeNavigator`` (and the ``NodeNavigator`` Protocol)."""

from __future__ import annotations

from shell.domain.entities.graph import Graph
from shell.domain.entities.graph_node import GraphNode
from shell.domain.services.node_navigator import LinearNodeNavigator
from shell.domain.value_objects.ids import GraphId, NodeId, TaskId, TemplateGraphId
from shell.domain.value_objects.mode import Mode


def _node(node_id: str, position: int, mode: str = "agent") -> GraphNode:
    return GraphNode(
        id=NodeId(node_id),
        position=position,
        node_dir=f"/fake/{node_id}",
        mode=Mode(mode),
        role=mode,
        node_type=mode,
    )


def _graph(*nodes: GraphNode) -> Graph:
    return Graph(
        id=GraphId.generate(),
        task_id=TaskId.generate(),
        template_graph_id=TemplateGraphId("tpl"),
        raw_dict={},
        nodes=list(nodes),
    )


class TestLinearNodeNavigatorFirst:
    def test_first_returns_lowest_position(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("b", 1), _node("a", 0), _node("c", 2))
        result = nav.first(graph)
        assert result is not None
        assert result.id == NodeId("a")

    def test_first_on_empty_graph_returns_none(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph()
        assert nav.first(graph) is None

    def test_first_handles_unsorted_input(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("z", 5), _node("y", 3), _node("x", 1))
        first = nav.first(graph)
        assert first is not None
        assert first.id == NodeId("x")


class TestLinearNodeNavigatorNextAfter:
    def test_next_after_returns_following_node(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("a", 0), _node("b", 1), _node("c", 2))
        nxt = list(nav.next_after(graph, NodeId("a")))
        assert len(nxt) == 1
        assert nxt[0].id == NodeId("b")

    def test_next_after_last_node_returns_empty(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("a", 0), _node("b", 1))
        assert list(nav.next_after(graph, NodeId("b"))) == []

    def test_next_after_unknown_node_returns_empty(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("a", 0))
        assert list(nav.next_after(graph, NodeId("ghost"))) == []

    def test_next_after_respects_position_ordering(self) -> None:
        nav = LinearNodeNavigator()
        # Out-of-order list, but ordering must follow ``position``.
        graph = _graph(_node("c", 2), _node("a", 0), _node("b", 1))
        nxt = list(nav.next_after(graph, NodeId("a")))
        assert nxt and nxt[0].id == NodeId("b")
        nxt2 = list(nav.next_after(graph, NodeId("b")))
        assert nxt2 and nxt2[0].id == NodeId("c")
