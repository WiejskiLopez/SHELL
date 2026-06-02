"""_init_app_node.py
Responsible for one thing: initialising the Node instance and creating
the node directory structure for the current App node.
"""

from __future__ import annotations

from shell.utils.path.path import Path


def _init_app_node(app) -> None:
    cli_properties = app.cli_.cli_properties_
    node_dir = cli_properties.node_dir_ or str(Path.resolve(cli_properties.runner_root_dir_ / ".node"))
    app.app_node_.node_.init_node(node_dir=node_dir)
