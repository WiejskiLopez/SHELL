from __future__ import annotations

from shell.component.config.config.internal._append_config_value import _append_config_value


def _append_config_dict(config: object, config_dict: dict, source: str) -> None:
    for key, value in config_dict.items():
        if value is not None:
            _append_config_value(config, key, value, source)
