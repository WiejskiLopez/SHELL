from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _init_app_config(app: App) -> None:
    app.append_app_config(app.runtime_.runtime_config_.config_dict_, source='runtime')
    app.append_app_config(app.cli_.cli_config_.config_dict_, source='cli')
    app.append_app_config(app.app_node_.node_.node_config_.config_.config_dict_, source='node')
