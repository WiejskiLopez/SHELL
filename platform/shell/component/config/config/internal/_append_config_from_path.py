from __future__ import annotations

import yaml

from shell.component.config.config.internal._append_config_dict import _append_config_dict
from shell.utils.path.path import Path, PathType


def _append_config_from_path(config: object, config_path: PathType | str, source: str) -> None:
    config._config_path = Path.new(config_path)
    if not Path.is_file(config._config_path):
        return
    raw = yaml.safe_load(Path.read_text(config._config_path)) or {}
    _append_config_dict(config, raw, source)
