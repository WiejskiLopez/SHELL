from shell.utils.path.path import PathType
"""router_stage.py
RouterStage — high-level stage management logic for the router node.

Slots:
    _app — parent App (DOM back-reference)

Delegates all physical I/O to NodeStage via app.app_node_.node_.node_stage_.
"""

from __future__ import annotations


from shell.structure.node.node_stage.node_stage import NodeStage


class RouterStage:
    """High-level stage logic for the router — delegates physical I/O to NodeStage."""

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    @property
    def node_stage_(self) -> NodeStage:
        return self._app.app_node_.node_.node_stage_
