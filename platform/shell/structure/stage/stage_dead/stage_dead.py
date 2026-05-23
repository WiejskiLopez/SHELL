from shell.utils.path.path import PathType
from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.stage.stage_dead.internal._init_stage_dead import _init_stage_dead
from shell.structure.stage.stage_dead.internal._clean_stage_dead import _clean_stage_dead


class StageDead:

    __slots__ = ("_app", "_dead_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._dead_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def dead_dir_(self) -> PathType:
        return self._dead_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_stage_dead(self) -> None:
        _init_stage_dead(self)
        self._module_status = ModuleStatus.INIT

    def clean_stage_dead(self) -> None:
        _clean_stage_dead(self)
