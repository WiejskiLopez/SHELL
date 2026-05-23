from shell.utils.path.path import PathType
from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.stage.stage_done.internal._init_stage_done import _init_stage_done
from shell.structure.stage.stage_done.internal._clean_stage_done import _clean_stage_done
from shell.structure.stage.stage_done.internal._save_stage_done import _save_stage_done
from shell.structure.stage.stage_done.internal._get_stage_done_last_message import _get_stage_done_last_message


class StageDone:

    __slots__ = ("_app", "_done_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._done_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def done_dir_(self) -> PathType:
        return self._done_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_stage_done(self) -> None:
        _init_stage_done(self)
        self._module_status = ModuleStatus.INIT

    def clean_stage_done(self) -> None:
        _clean_stage_done(self)

    def save_stage_done(self, file: PathType) -> None:
        _save_stage_done(self, file)

    def get_stage_done_last_message(self) -> PathType | None:
        return _get_stage_done_last_message(self)
