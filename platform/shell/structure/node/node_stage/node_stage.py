"""node_stage.py
NodeStage — physical stage directory I/O for a single node.

Slots:
    _stage_dir     — resolved path to the stage directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_stage()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_stage.internal._init_node_stage import _init_node_stage
from shell.structure.node.node_stage.internal._clean_node_stage import _clean_node_stage
from shell.structure.node.node_stage.internal._move_to_pending import _move_to_pending
from shell.structure.node.node_stage.internal._move_pending_to_history import _move_pending_to_history
from shell.structure.node.node_stage.internal._move_to_history import _move_to_history
from shell.structure.node.node_stage.internal._move_to_ignored import _move_to_ignored
from shell.structure.node.node_stage.internal._move_to_dead import _move_to_dead
from shell.structure.stage.stage.stage import Stage
from shell.structure.stage.stage_active.stage_active import StageActive
from shell.structure.stage.stage_pending.stage_pending import StagePending
from shell.structure.stage.stage_history.stage_history import StageHistory
from shell.structure.stage.stage_ignored.stage_ignored import StageIgnored
from shell.structure.stage.stage_dead.stage_dead import StageDead
from shell.structure.stage.stage_done.stage_done import StageDone


class NodeStage:
    """Physical stage directory I/O — active, pending, history, ignored, dead, done subdirs."""

    __slots__ = ("_app", "_stage_dir", "_module_status", "_stage")

    def __init__(self, app) -> None:
        self._app = app
        self._stage_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._stage: Stage | None = None

    @property
    def stage_dir_(self) -> PathType:
        return self._stage_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    @property
    def stage_(self) -> Stage:
        if self._stage is None:
            self._stage = Stage(self._stage_dir, self._app)
        return self._stage

    @property
    def stage_active_(self) -> StageActive:
        return self.stage_.stage_active_

    @property
    def stage_pending_(self) -> StagePending:
        return self.stage_.stage_pending_

    @property
    def stage_history_(self) -> StageHistory:
        return self.stage_.stage_history_

    @property
    def stage_ignored_(self) -> StageIgnored:
        return self.stage_.stage_ignored_

    @property
    def stage_dead_(self) -> StageDead:
        return self.stage_.stage_dead_

    @property
    def stage_done_(self) -> StageDone:
        return self.stage_.stage_done_

    def init_node_stage(self) -> None:
        _init_node_stage(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_stage(self) -> None:
        _clean_node_stage(self)

    def save_to_active(self, file: PathType, dest_name: str | None = None) -> None:
        self.stage_active_.save_stage_active(file, dest_name)

    def save_to_pending(self, file: PathType) -> None:
        self.stage_pending_.save_stage_pending(file)

    def save_to_history(self, file: PathType) -> None:
        self.stage_history_.save_stage_history(file)

    def save_to_done(self, file: PathType) -> None:
        self.stage_done_.save_stage_done(file)

    def move_to_pending(self, filename: str) -> None:
        _move_to_pending(self, filename)

    def move_pending_to_history(self, filename: str) -> None:
        _move_pending_to_history(self, filename)

    def move_to_history(self, filename: str) -> None:
        _move_to_history(self, filename)

    def move_to_ignored(self, filename: str) -> None:
        _move_to_ignored(self, filename)

    def move_to_dead(self, filename: str) -> None:
        _move_to_dead(self, filename)

    def get_active_files(self) -> list[PathType]:
        return self.stage_active_.get_stage_active_files()

    def get_pending_files(self) -> list[PathType]:
        return self.stage_pending_.get_stage_pending_files()

    def get_last_message(self) -> PathType | None:
        return self.stage_done_.get_stage_done_last_message()

