"""node_logs.py
NodeLogs: manages the logs directory for a single node run.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_logs()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_logs.internal._clean_node_logs import _clean_node_logs
from shell.structure.node.node_logs.internal._init_node_logs import _init_node_logs

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


class NodeLogs:
    """Manages the logs directory for a single node run.

    Slots:
        _app            — parent App
        _module_status  — ModuleStatus; NEW until init_node_logs() is called
    """

    __slots__ = ("_app", "_logs_dir", "_module_status")

    def __init__(self, app: 'App') -> None:
        self._app = app
        self._logs_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def logs_dir_(self) -> PathType:
        return self._logs_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_logs(self) -> None:
        _init_node_logs(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_logs(self) -> None:
        _clean_node_logs(self)
