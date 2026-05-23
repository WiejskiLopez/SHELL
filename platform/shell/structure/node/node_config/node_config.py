"""node_config.py
NodeConfig — loader and holder for node_dir/.node/config/config.yaml.

Slots:
    _app           — parent App (DOM back-reference)
    _config        — Config instance (Config | None)
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_config()

Responsibilities:
    Reads config.yaml from the node directory into a Config object.
    Can also be initialised from data (role, type) without reading from disk.
"""

from __future__ import annotations

from shell.component.config.config.config import Config
from shell.status.module_status.module_status import ModuleStatus
from shell.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML

class NodeConfig:
    """Holds Config object for the node directory.

    Cached via app.node_config_. _config is populated
    by init_node_config() or append_node_config().
    """

    __slots__ = ("_app", "_config", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._config: Config | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    # -----------------------------------------------------------------------
    # Validated property
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init_node_config(self) -> None:
        cfg_path = self.config_dir_ / CONFIG_YAML
        self.config_.init_config(cfg_path, source='node')
        self._module_status = ModuleStatus.INIT
