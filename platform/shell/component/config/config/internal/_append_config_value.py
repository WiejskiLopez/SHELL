from __future__ import annotations

import yaml

from typing import Literal

from shell.utils.path.path import Path


def _append_config_value(config: 'Config', key: str, value, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
    if config._config_dict is None:
        config._config_dict = {}
    existing = config._config_dict.get(key)
    if existing is None:
        config._config_dict[key] = {'value': value, 'source': source}
    elif source == 'cli':
        config._config_dict[key] = {'value': value, 'source': source}
    elif source == 'sub_node' and existing['source'] in ('runtime', 'node'):
        config._config_dict[key] = {'value': value, 'source': source}
    elif source == 'node' and existing['source'] == 'runtime':
        config._config_dict[key] = {'value': value, 'source': source}
    if config._config_path is not None:
        flat = {k: v['value'] for k, v in config._config_dict.items()}
        Path.write_text(config._config_path, yaml.dump(flat, default_flow_style=False, allow_unicode=True))
