from shell.utils.path.path import PathType
from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.stage.stage_ignored.internal._init_stage_ignored import _init_stage_ignored
from shell.structure.stage.stage_ignored.internal._clean_stage_ignored import _clean_stage_ignored


class StageIgnored:

    __slots__ = ("_app", "_ignored_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._ignored_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def ignored_dir_(self) -> PathType:
        return self._ignored_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_stage_ignored(self) -> None:
        _init_stage_ignored(self)
        self._module_status = ModuleStatus.INIT

    def clean_stage_ignored(self) -> None:
        _clean_stage_ignored(self)
