"""node_temp.py
NodeTemp — temp directory for a single node.

Slots:
    _temp_dir      — path to the temp directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_temp()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_temp.internal._init_temp_dir import _init_temp_dir
from shell.structure.node.node_temp.internal._clean_node_temp import _clean_node_temp


class NodeTemp:
    """Manages the temp directory for a single node run."""

    __slots__ = ("_app", "_temp_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._temp_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def temp_dir_(self) -> PathType:
        return self._temp_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_temp(self) -> None:
        _init_temp_dir(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_temp(self) -> None:
        _clean_node_temp(self)
