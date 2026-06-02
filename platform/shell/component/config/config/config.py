"""config.py
Config: in-memory holder for module configuration loaded from runner_config DB.

Config is never read from or written to the filesystem at runtime.
Bootstrap of YAML seed files into DB is handled by RunnerConfigRepo.

Slots:
    _app         — parent App (DOM back-reference)
    _config_dict — parsed config dict {key: {'value', 'source'}}
"""

from __future__ import annotations

from typing import Literal

from shell.component.config.config.internal._append_config_dict import _append_config_dict
from shell.component.config.config.internal._append_config_value import _append_config_value
from shell.component.config.config.internal._init_config import _init_config


class Config:
    """In-memory configuration for a single node run, sourced from runner_config DB."""

    __slots__ = ("_app", "_config_dict")

    def __init__(self, app=None) -> None:
        self._app = app
        self._config_dict: dict | None = None

    @property
    def config_dict_(self) -> dict:
        if not self._config_dict:
            return {}
        return {k: v['value'] for k, v in self._config_dict.items()}

    def init_config(self, package_name: str, kind: str, source: str, seed_yaml_path=None) -> None:
        _init_config(self, package_name, kind, source, seed_yaml_path)

    def append_config_value(self, key: str, value, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_value(self, key, value, source)

    def append_config_dict(self, config_dict: dict, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_dict(self, config_dict, source)
