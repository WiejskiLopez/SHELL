from shell.utils.path.path import PathType
from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.stage.stage_active.internal._init_stage_active import _init_stage_active
from shell.structure.stage.stage_active.internal._clean_stage_active import _clean_stage_active
from shell.structure.stage.stage_active.internal._save_stage_active import _save_stage_active
from shell.structure.stage.stage_active.internal._get_stage_active_files import _get_stage_active_files


class StageActive:

    __slots__ = ("_app", "_active_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._active_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def active_dir_(self) -> PathType:
        return self._active_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_stage_active(self) -> None:
        _init_stage_active(self)
        self._module_status = ModuleStatus.INIT

    def clean_stage_active(self) -> None:
        _clean_stage_active(self)

    def save_stage_active(self, file: PathType, dest_name: str | None = None) -> None:
        _save_stage_active(self, file, dest_name)

    def get_stage_active_files(self) -> list[PathType]:
        return _get_stage_active_files(self)
