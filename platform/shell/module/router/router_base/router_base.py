"""router_base.py
RouterBase: holds task files loaded from .node/task for every router node.

Slots:
    _app                 — parent App (back-reference)
    _graph            — Optional; lazy Graph instance
    _role_to_node_map    — dict[role, node] built from graph (dict | None)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.graph.graph.graph import Graph
from shell.module.router.router_base.internal._assert_node_in_graph import _assert_node_in_graph
from shell.module.router.router_base.internal._init_router_base import _init_router_base


class RouterBase:
    """Holds task files and graph state for any router node."""

    __slots__ = ("_app", "_graph", "_role_to_node_map")

    def __init__(self, app=None) -> None:
        self._app = app
        self._graph = None
        self._role_to_node_map: dict | None = None
    @property
    def graph_(self) -> Graph:
        if self._graph is None:
            self._graph = Graph(self._app)
        return self._graph

    @property
    def graph_nodes_(self):
        return self.graph_.sub_nodes_

    @property
    def role_to_node_map_(self) -> dict:
        if self._role_to_node_map is None:
            self._role_to_node_map = {n.role_: n for n in self.graph_nodes_ if n.role_}
        return self._role_to_node_map

    def get_current_graph_node_index(self, node_name: str) -> int:
        index = next(
            (i for i, n in enumerate(self.graph_nodes_) if n.node_name_ == node_name),
            None,
        )
        _assert_node_in_graph(index, node_name)
        return index

    def get_next_graph_node(self, node_name: str):
        index = self.get_current_graph_node_index(node_name)
        graph_nodes = self.graph_nodes_
        return graph_nodes[index + 1] if index + 1 < len(graph_nodes) else None

    def get_prev_graph_node(self, node_name: str):
        index = self.get_current_graph_node_index(node_name)
        return self.graph_nodes_[index - 1] if index > 0 else None

    def init_router_base(self, reader=None) -> None:
        _init_router_base(self, reader=reader)
