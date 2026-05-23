"""_init_node_config.py
Private. Responsible for one thing: reading config.yaml into NodeConfig._config.
"""

from __future__ import annotations

from shell.app.app.app import App


def _init_node_config(app: App) -> None:
    app.node_config_.init_node_config()
