"""app_node.py
AppNode: structured value object for the current node in the context of App.

Analogous to SubNode (which represents a single node in a graph),
AppNode represents the single node that this App instance is executing.

Slots:
    _app  — parent App (DOM back-reference)
    _node — Optional; Node instance, set during init_app_node()

Validated properties:
    node_dir_        — resolved Path to the node directory
    node_name_       — node directory name (== unique node identifier)
    node_config_     — lazy NodeConfig instance

Methods:
    init_app_node() — create Node from CLI args + node directory structure
"""

from __future__ import annotations

from shell.structure.node.node.node import Node
from shell.app.app_node.internal._init_app_node import _init_app_node


class AppNode:
    """Structured value object for the current node in the context of App."""

    __slots__ = ("_app", "_node")

    def __init__(self, app) -> None:
        self._app = app
        self._node: Node | None = None

    # -----------------------------------------------------------------------
    # Node facade
    # -----------------------------------------------------------------------

    @property
    def node_(self) -> Node:
        if self._node is None:
            self._node = Node(self._app)
        return self._node

    # -----------------------------------------------------------------------
    # Phase method
    # -----------------------------------------------------------------------

    def init_app_node(self) -> None:
        _init_app_node(self._app)

    def release_node(self, rmtree=None, unlink=None) -> None:
        if self._app.runner_.mode_ != 'router':
            self._node.clean_node(rmtree=rmtree, unlink=unlink)
