"""graph_status.py
GraphStatus — derives overall graph status from node statuses.

Slots:
    _graph    — parent Graph instance (back-reference)
    _app  — parent App instance (back-reference)

Validated properties:
    graph_status_  — overall Status derived from node statuses
"""

from __future__ import annotations

from shell.status.status import Status

_STATUS_PRIORITY = (
    Status.ERROR,
    Status.LOCKED,
    Status.TIMEOUT,
    Status.WAITING,
    Status.QUESTION,
)
_SUCCESS_STATES = frozenset({Status.SUCCESS, Status.SKIP})


class GraphStatus:
    """Derives overall graph status from node statuses (priority order).

    Priority: ERROR > LOCKED > TIMEOUT > WAITING > QUESTION > SUCCESS.
    Returns Status.SUCCESS only when all nodes are in {SUCCESS, SKIP}.
    """

    __slots__ = ("_graph", "_app")

    def __init__(self, graph) -> None:
        self._graph = graph
        self._app = graph._app

    @property
    def graph_status_(self) -> Status:
        """Derive overall graph status from node statuses (priority order)."""
        sub_nodes = self._graph.sub_nodes_
        statuses = {n.node_.status_ for n in sub_nodes}
        for s in _STATUS_PRIORITY:
            if s in statuses:
                return s
        if all(n.node_.status_ in _SUCCESS_STATES for n in sub_nodes):
            return Status.SUCCESS
        for node in sub_nodes:
            if node.node_.status_ not in _SUCCESS_STATES:
                return node.node_.status_
        return Status.SUCCESS
