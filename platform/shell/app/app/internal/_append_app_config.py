from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from shell.app.app.app import App


def _append_app_config(app: App, config_dict: dict, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
    app.app_config_.append_config_dict(config_dict, source)
    app.placeholders_.bind_dict(app.app_config_.config_dict_)
