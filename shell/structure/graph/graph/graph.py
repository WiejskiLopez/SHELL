from __future__ import annotations

from shell.structure.graph.graph.internal._init_graph import _init_graph
from shell.structure.sub_node.sub_node.sub_node import SubNode
from shell.status.status import Status


class Graph:
    """Graph nodes loaded from a task YAML.

    ``self.graph_nodes`` is an empty list until ``init_graph`` is called,
    at which point it is populated as ``list[SubNode]`` from ``task_graph_yaml``.

    Supports iteration, len, and indexing so it can be used directly
    wherever a sequence of graph nodes is expected.
    """

    __slots__ = ("_sub_nodes", "_app", "_status")

    def __init__(self, app=None) -> None:
        self._sub_nodes: list[SubNode] = []
        self._app = app
        self._status: Status = Status.NULL

    @property
    def status_(self) -> Status:
        return self._status

    # ------------------------------------------------------------------ #
    # Sequence protocol                                                    #
    # ------------------------------------------------------------------ #

    def __iter__(self):
        return iter(self._sub_nodes)

    def __len__(self) -> int:
        return len(self._sub_nodes)

    def __getitem__(self, index):
        return self._sub_nodes[index]

    # ------------------------------------------------------------------ #
    # Pure queries                                                         #
    # ------------------------------------------------------------------ #

    @property
    def sub_nodes_(self) -> list:
        return self._sub_nodes

    # ------------------------------------------------------------------ #
    # Mutating operations                                                  #
    # ------------------------------------------------------------------ #

    def init_graph(
        self,
        reader=None,
        writer=None,
    ) -> None:
        _init_graph(self, reader=reader, writer=writer)
