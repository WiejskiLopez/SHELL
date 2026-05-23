from shell.utils.path.path import PathType
from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.stage.stage_pending.internal._init_stage_pending import _init_stage_pending
from shell.structure.stage.stage_pending.internal._clean_stage_pending import _clean_stage_pending
from shell.structure.stage.stage_pending.internal._save_stage_pending import _save_stage_pending
from shell.structure.stage.stage_pending.internal._get_stage_pending_files import _get_stage_pending_files


class StagePending:

    __slots__ = ("_app", "_pending_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._pending_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def pending_dir_(self) -> PathType:
        return self._pending_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_stage_pending(self) -> None:
        _init_stage_pending(self)
        self._module_status = ModuleStatus.INIT

    def clean_stage_pending(self) -> None:
        _clean_stage_pending(self)

    def save_stage_pending(self, file: PathType) -> None:
        _save_stage_pending(self, file)

    def get_stage_pending_files(self) -> list[PathType]:
        return _get_stage_pending_files(self)
