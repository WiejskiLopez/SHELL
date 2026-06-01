"""node_scripts.py
NodeScripts — scripts directory for a single node.

Slots:
    _scripts_dir   — path to the scripts directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_scripts()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_scripts.internal._init_scripts_dir import _init_scripts_dir
from shell.structure.node.node_scripts.internal._clean_node_scripts import _clean_node_scripts


class NodeScripts:
    """Manages the scripts directory for a single node run."""

    __slots__ = ("_app", "_scripts_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._scripts_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def scripts_dir_(self) -> PathType:
        return self._scripts_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_scripts(self) -> None:
        _init_scripts_dir(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_scripts(self) -> None:
        _clean_node_scripts(self)
