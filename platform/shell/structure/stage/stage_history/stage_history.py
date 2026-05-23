from shell.utils.path.path import PathType
from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.stage.stage_history.internal._init_stage_history import _init_stage_history
from shell.structure.stage.stage_history.internal._clean_stage_history import _clean_stage_history
from shell.structure.stage.stage_history.internal._save_stage_history import _save_stage_history


class StageHistory:

    __slots__ = ("_app", "_history_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._history_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def history_dir_(self) -> PathType:
        return self._history_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_stage_history(self) -> None:
        _init_stage_history(self)
        self._module_status = ModuleStatus.INIT

    def clean_stage_history(self) -> None:
        _clean_stage_history(self)

    def save_stage_history(self, file: PathType) -> None:
        _save_stage_history(self, file)
