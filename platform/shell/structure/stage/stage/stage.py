from shell.utils.path.path import PathType
"""stage.py
Stage — groups all stage sub-directories for a single node.

Slots:
    _stage_dir      — resolved path to the stage root directory
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_stage()
    _stage_active   — Optional; StageActive lazy instance
    _stage_pending  — Optional; StagePending lazy instance
    _stage_history  — Optional; StageHistory lazy instance
    _stage_ignored  — Optional; StageIgnored lazy instance
    _stage_dead     — Optional; StageDead lazy instance
    _stage_done     — Optional; StageDone lazy instance
"""

from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.stage.stage.internal._init_stage import _init_stage
from shell.structure.stage.stage_active.stage_active import StageActive
from shell.structure.stage.stage_pending.stage_pending import StagePending
from shell.structure.stage.stage_history.stage_history import StageHistory
from shell.structure.stage.stage_ignored.stage_ignored import StageIgnored
from shell.structure.stage.stage_dead.stage_dead import StageDead
from shell.structure.stage.stage_done.stage_done import StageDone


class Stage:

    __slots__ = (
        "_app",
        "_stage_dir",
        "_module_status",
        "_stage_active",
        "_stage_pending",
        "_stage_history",
        "_stage_ignored",
        "_stage_dead",
        "_stage_done",
    )

    def __init__(self, stage_dir: PathType, app) -> None:
        self._app = app
        self._stage_dir: PathType = stage_dir
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._stage_active: StageActive | None = None
        self._stage_pending: StagePending | None = None
        self._stage_history: StageHistory | None = None
        self._stage_ignored: StageIgnored | None = None
        self._stage_dead: StageDead | None = None
        self._stage_done: StageDone | None = None

    @property
    def stage_dir_(self) -> PathType:
        return self._stage_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    @property
    def stage_active_(self) -> StageActive:
        if self._stage_active is None:
            self._stage_active = StageActive(self._app)
        return self._stage_active

    @property
    def stage_pending_(self) -> StagePending:
        if self._stage_pending is None:
            self._stage_pending = StagePending(self._app)
        return self._stage_pending

    @property
    def stage_history_(self) -> StageHistory:
        if self._stage_history is None:
            self._stage_history = StageHistory(self._app)
        return self._stage_history

    @property
    def stage_ignored_(self) -> StageIgnored:
        if self._stage_ignored is None:
            self._stage_ignored = StageIgnored(self._app)
        return self._stage_ignored

    @property
    def stage_dead_(self) -> StageDead:
        if self._stage_dead is None:
            self._stage_dead = StageDead(self._app)
        return self._stage_dead

    @property
    def stage_done_(self) -> StageDone:
        if self._stage_done is None:
            self._stage_done = StageDone(self._app)
        return self._stage_done

    def init_stage(self) -> None:
        _init_stage(self)
        self._module_status = ModuleStatus.INIT
