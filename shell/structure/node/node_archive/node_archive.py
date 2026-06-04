"""node_archive.py  (node_archive)
NodeArchive — single entry point for all node archive operations.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_archive()

Methods:
    save_archive(clock)     — write archive ZIP; never raises
"""

from __future__ import annotations

from shell.utils.path.path import PathType

from collections.abc import Callable
from datetime import datetime

from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_archive.internal._save_archive_zip import _save_archive_zip
from shell.structure.node.node_archive.internal._clean_node_archive import _clean_node_archive
from shell.constants.constants import DOT_NODE, DIR_ARCHIVE

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


class NodeArchive:
    """Typed interface for node archive operations.

    Slots:
        _app            — parent App
        _module_status  — ModuleStatus; NEW until init_node_archive() is called
    """

    __slots__ = ("_app", "_module_status")

    def __init__(self, app: 'App') -> None:
        self._app = app
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def node_archive_dir_(self) -> PathType:
        return Path.resolve(self._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_ARCHIVE)

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_archive(self) -> None:
        self._module_status = ModuleStatus.INIT

    def clean_node_archive(self) -> None:
        _clean_node_archive(self)

    def save_archive(self, clock: Callable[[], datetime] | None = None) -> None:
        """Write archive ZIP.  Never raises — errors are logged and suppressed.

        clock: optional callable () -> datetime (defaults to datetime.now(utc)).
        """
        try:
            node_archive_dir = self.node_archive_dir_
            runner_result = self._app.result_.runner_result_
            self._app.app_trace_.record_info('node_archive.NodeArchive.save_archive', f'archive_dir={node_archive_dir}')
            self._app.app_trace_.record_info('node_archive.NodeArchive.save_archive', f'runner_result={runner_result}')
            _save_archive_zip(node_archive_dir, runner_result, clock=clock, trace=self._app.app_trace_)
            self._app.app_trace_.record_info('node_archive.NodeArchive.save_archive', 'archive zip written')
        except Exception as exc:
            self._app.app_trace_.record_error('node_archive.NodeArchive.save_archive', exc)
