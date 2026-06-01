"""config.py
Config: holder for the default config.yaml loaded from runner_root_dir.

Slots:
    _app         — parent App (DOM back-reference)
    _config_path — path to the config.yaml file on disk
    _config_dict — parsed YAML dict
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from typing import Literal

from shell.component.config.config.internal._append_config_dict import _append_config_dict
from shell.component.config.config.internal._append_config_from_path import _append_config_from_path
from shell.component.config.config.internal._append_config_value import _append_config_value
from shell.component.config.config.internal._assert_config_path_set import _assert_config_path_set
from shell.component.config.config.internal._assert_model_set import _assert_model_set
from shell.component.config.config.internal._init_config import _init_config


class Config:
    """Raw default config.yaml for a single node run.

    Constructed as Config(app) — held as app.config_,
    loaded once during init_app_configuration().
    """

    __slots__ = ("_app", "_config_path", "_config_dict")

    def __init__(
        self,
        app=None,
        config_path: PathType | str | None = None,
    ) -> None:
        self._app = app
        self._config_path: PathType | None = Path.new(config_path) if config_path else None
        self._config_dict: dict | None = None

    @property
    def config_dict_(self) -> dict:
        if not self._config_dict:
            return {}
        return {k: v['value'] for k, v in self._config_dict.items()}

    @property
    def config_path_(self) -> PathType:
        _assert_config_path_set(self._config_path)
        return Path.new(self._config_path).resolve()

    def init_config(self, config_path: PathType | str, source: str) -> None:
        _init_config(self, config_path, source)

    def append_config_value(self, key: str, value, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_value(self, key, value, source)

    def append_config_dict(self, config_dict: dict, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_dict(self, config_dict, source)

    def append_config_from_path(self, config_path: PathType | str, source: Literal['cli', 'sub_node', 'node', 'runtime']) -> None:
        _append_config_from_path(self, config_path, source)
