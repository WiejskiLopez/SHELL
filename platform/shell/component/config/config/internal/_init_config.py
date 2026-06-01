from __future__ import annotations

import yaml

from shell.utils.path.path import Path, PathType


def _init_config(config: 'Config', config_path: PathType | str, source: str) -> None:
    config_path = Path.new(config_path)
    try:
        config._config_path = config_path
        raw = yaml.safe_load(Path.read_text(config_path)) or {}
        config._config_dict = {k: {'value': v, 'source': source} for k, v in raw.items()}
    except Exception as exc:
        config._app.app_trace_.record_error_and_raise('config.Config.init_config', exc)
