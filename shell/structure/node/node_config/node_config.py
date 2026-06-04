"""node_config.py
NodeConfig — loader and holder for node-level configuration sourced from runner_config DB.

The seed file <node_dir>/.node/config/config.yaml is used only as a one-time bootstrap
seed; runtime always reads from the DB (kind='node_config', package_name=node_name).

Slots:
    _app           — parent App (DOM back-reference)
    _config        — Config instance (Config | None)
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_config()
"""

from __future__ import annotations

from shell.component.config.config.config import Config
from shell.status.module_status.module_status import ModuleStatus
from shell.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML
from shell.utils.path.path import PathType

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App

class NodeConfig:
    """Holds Config object for the running node, sourced from runner_config DB."""

    __slots__ = ("_app", "_config", "_module_status")

    def __init__(self, app: 'App') -> None:
        self._app = app
        self._config: Config | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def config_(self) -> Config:
        if self._config is None:
            self._config = Config(self._app)
        return self._config

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    @property
    def config_dir_(self) -> PathType:
        return self._app.app_node_.node_.node_dir_ / DOT_NODE / CONFIG_DIR

    def init_node_config(self) -> None:
        seed_path = self.config_dir_ / CONFIG_YAML
        package_name = self._app.app_node_.node_.node_name_
        self.config_.init_config(
            package_name=package_name,
            kind='node_config',
            source='node',
            seed_yaml_path=seed_path,
        )
        self._module_status = ModuleStatus.INIT
