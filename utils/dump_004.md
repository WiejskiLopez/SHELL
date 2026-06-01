### platform/shell/structure/stage/stage/stage.py
```
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

from shell.utils.path.path import PathType


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
```

### platform/shell/structure/stage/stage_active/__init__.py
```
```

### platform/shell/structure/stage/stage_active/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_active/internal/_clean_stage_active.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_active(stage_active) -> None:
    active_dir = stage_active.active_dir_
    if not Path.exists(active_dir):
        return
    for item in Path.iterdir(active_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/stage/stage_active/internal/_get_stage_active_files.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _get_stage_active_files(stage_active) -> list[PathType]:
    from shell.module.router.router.parse_message_filename import parse_message_filename
    active_dir = stage_active.active_dir_
    if not Path.exists(active_dir):
        return []
    candidates = [f for f in Path.iterdir(active_dir) if Path.is_file(f)]

    def _msg_id_key(f: PathType) -> int:
        parsed = parse_message_filename(f.name)
        if parsed is None:
            return -1
        try:
            return int(parsed.sequence_id)
        except ValueError:
            return -1

    return sorted(candidates, key=_msg_id_key)
```

### platform/shell/structure/stage/stage_active/internal/_init_stage_active.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_ACTIVE


def _init_stage_active(stage_active) -> None:
    stage_active._active_dir = stage_active._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_ACTIVE
    Path.mkdir(stage_active.active_dir_)
```

### platform/shell/structure/stage/stage_active/internal/_save_stage_active.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_active(stage_active, file: PathType, dest_name: str | None = None) -> None:
    name = dest_name if dest_name is not None else file.name
    dest = stage_active.active_dir_ / name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_active/stage_active.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


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
```

### platform/shell/structure/stage/stage_dead/__init__.py
```
```

### platform/shell/structure/stage/stage_dead/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_dead/internal/_clean_stage_dead.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_dead(stage_dead) -> None:
    dead_dir = stage_dead.dead_dir_
    if not Path.exists(dead_dir):
        return
    for item in Path.iterdir(dead_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/stage/stage_dead/internal/_init_stage_dead.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_DEAD


def _init_stage_dead(stage_dead) -> None:
    stage_dead._dead_dir = stage_dead._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_DEAD
    Path.mkdir(stage_dead.dead_dir_)
```

### platform/shell/structure/stage/stage_dead/stage_dead.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


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
```

### platform/shell/structure/stage/stage_done/__init__.py
```
```

### platform/shell/structure/stage/stage_done/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_done/internal/_clean_stage_done.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_done(stage_done) -> None:
    done_dir = stage_done.done_dir_
    if not Path.exists(done_dir):
        return
    for item in Path.iterdir(done_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/stage/stage_done/internal/_get_stage_done_last_message.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _get_stage_done_last_message(stage_done) -> PathType | None:
    done_dir = stage_done.done_dir_
    if not Path.exists(done_dir):
        return None
    candidates = [f for f in Path.iterdir(done_dir) if Path.is_file(f)]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_mtime)
```

### platform/shell/structure/stage/stage_done/internal/_init_stage_done.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_DONE


def _init_stage_done(stage_done) -> None:
    stage_done._done_dir = stage_done._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_DONE
    Path.mkdir(stage_done.done_dir_)
```

### platform/shell/structure/stage/stage_done/internal/_save_stage_done.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_done(stage_done, file: PathType) -> None:
    dest = stage_done.done_dir_ / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_done/stage_done.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


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
```

### platform/shell/structure/stage/stage_history/__init__.py
```
```

### platform/shell/structure/stage/stage_history/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_history/internal/_clean_stage_history.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_history(stage_history) -> None:
    history_dir = stage_history.history_dir_
    if not Path.exists(history_dir):
        return
    for item in Path.iterdir(history_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/stage/stage_history/internal/_init_stage_history.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_HISTORY


def _init_stage_history(stage_history) -> None:
    stage_history._history_dir = stage_history._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_HISTORY
    Path.mkdir(stage_history.history_dir_)
```

### platform/shell/structure/stage/stage_history/internal/_save_stage_history.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_history(stage_history, file: PathType) -> None:
    dest = stage_history.history_dir_ / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_history/stage_history.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


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
```

### platform/shell/structure/stage/stage_ignored/__init__.py
```
```

### platform/shell/structure/stage/stage_ignored/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_ignored/internal/_clean_stage_ignored.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_ignored(stage_ignored) -> None:
    ignored_dir = stage_ignored.ignored_dir_
    if not Path.exists(ignored_dir):
        return
    for item in Path.iterdir(ignored_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/stage/stage_ignored/internal/_init_stage_ignored.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_IGNORED


def _init_stage_ignored(stage_ignored) -> None:
    stage_ignored._ignored_dir = stage_ignored._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_IGNORED
    Path.mkdir(stage_ignored.ignored_dir_)
```

### platform/shell/structure/stage/stage_ignored/stage_ignored.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


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
```

### platform/shell/structure/stage/stage_pending/__init__.py
```
```

### platform/shell/structure/stage/stage_pending/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_pending/internal/_clean_stage_pending.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_stage_pending(stage_pending) -> None:
    pending_dir = stage_pending.pending_dir_
    if not Path.exists(pending_dir):
        return
    for item in Path.iterdir(pending_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/stage/stage_pending/internal/_get_stage_pending_files.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _get_stage_pending_files(stage_pending) -> list[PathType]:
    pending_dir = stage_pending.pending_dir_
    if not Path.exists(pending_dir):
        return []
    return [f for f in Path.iterdir(pending_dir) if Path.is_file(f)]
```

### platform/shell/structure/stage/stage_pending/internal/_init_stage_pending.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_PENDING


def _init_stage_pending(stage_pending) -> None:
    stage_pending._pending_dir = stage_pending._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_PENDING
    Path.mkdir(stage_pending.pending_dir_)
```

### platform/shell/structure/stage/stage_pending/internal/_save_stage_pending.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_pending(stage_pending, file: PathType) -> None:
    dest = stage_pending.pending_dir_ / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_pending/stage_pending.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


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
```

### platform/shell/structure/sub_node/__init__.py
```
```

### platform/shell/structure/sub_node/sub_node/internal/__init__.py
```
```

### platform/shell/structure/sub_node/sub_node/internal/_assert_entrypoint_exists.py
```
"""_assert_entrypoint_exists.py
Responsible for one thing: raising FileNotFoundError when entrypoint.py is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_entrypoint_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[SubNode] entrypoint not found: {path}")
```

### platform/shell/structure/sub_node/sub_node/internal/_assert_node_dir_exists.py
```
"""_assert_node_dir_exists.py
Responsible for one thing: raising FileNotFoundError when the node directory is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_node_dir_exists(path: PathType) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[sub_node] node dir not found: {path}")
```

### platform/shell/structure/sub_node/sub_node/internal/_assert_node_name_set.py
```
"""_assert_node_name_set.py
Responsible for one thing: raising ValueError when _node_name is not set.
"""


def _assert_node_name_set(node_name: str | None) -> None:
    """Raise ValueError if node_name is falsy."""
    if not node_name:
        raise ValueError("[SubNode] _node_name is not set")
```

### platform/shell/structure/sub_node/sub_node/internal/_init_sub_node.py
```
from __future__ import annotations

from shell.component.config.config.config import Config
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK
from shell.status.status import Status


def _init_sub_node(sub_node, sub_node_config_dict, writer, reader) -> None:
    config = Config(sub_node._app)
    config.append_config_dict(sub_node_config_dict, 'sub_node')
    sub_node._sub_node_config = config
    sub_node.sub_node_properties_.init_sub_node_properties(
        sub_node_config_dict,
        writer=writer,
    )
    task_dir = (sub_node._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    sub_node.init_sub_node_command(task_dir)
    sub_node.node_status_.init_status(sub_node_config_dict.get('status'))
    if sub_node.status_ == Status.NULL:
        sub_node.node_status_.set_status(Status.INITIALIZED)
        sub_node_config_dict['status'] = Status.INITIALIZED.name
        config.append_config_value('status', Status.INITIALIZED.name, 'sub_node')
```

### platform/shell/structure/sub_node/sub_node/internal/_run_sub_node.py
```
"""_run_sub_node.py
Responsible for one thing: invoking a runner on a single task node via subprocess
and updating the node status.
"""

import os
import subprocess

from shell.status.status import Status


def _run_sub_node(sub_node, task_dir, app, runner=None) -> Status:
    """Invoke the configured runner on this task node and update its status.

    Returns the resulting Status, or raises on fatal error.

    runner: optional callable (cmd, **kwargs) -> CompletedProcess for testability.
    """
    if runner is None:
        runner = subprocess.run

    command = sub_node.sub_node_command_.command_
    app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"running node {sub_node.node_name_} \u2192 {command}")

    try:
        proc = runner(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env={**os.environ, 'PYTHONUTF8': '1'},
            cwd=str(sub_node.entrypoint_path_.parent),
        )
        sub_node.node_status_.set_status(proc.returncode)
        app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"node {sub_node.node_name_} finished (rc={proc.returncode})", stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
        if proc.returncode != 0 and proc.stderr:
            app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"node {sub_node.node_name_} stderr: {proc.stderr.strip()}")
        if proc.returncode != 0 and proc.stdout:
            app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"node {sub_node.node_name_} stdout: {proc.stdout.strip()}")
        return sub_node.status_
    except Exception as exc:
        sub_node.node_status_.set_status(Status.ERROR)
        app.app_trace_.record_error_and_raise('sub_node._run_sub_node._run_sub_node', exc)
```

### platform/shell/structure/sub_node/sub_node/sub_node.py
```
"""sub_node.py
SubNode: structured value object for a single graph node.

Slots:
    _app                  -- parent App (DOM back-reference)
    _sub_node_config      -- Config instance loaded from graph node entry
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.utils.io.io import default_make_dirs, default_read_utf8, default_write_utf8
from shell.component.config.config.config import Config
from shell.structure.sub_node.sub_node.internal._assert_entrypoint_exists import _assert_entrypoint_exists
from shell.structure.sub_node.sub_node.internal._init_sub_node import _init_sub_node
from shell.structure.sub_node.sub_node.internal._run_sub_node import _run_sub_node
from shell.structure.sub_node.sub_node_command.sub_node_command import SubNodeCommand
from shell.structure.sub_node.sub_node_properties.sub_node_properties import SubNodeProperties
from shell.structure.node.node_status.node_status import NodeStatus
from shell.status.status import Status


class SubNode:
    """Structured value object for a single graph node."""

    __slots__ = ("_app", "_sub_node_config", "_sub_node_command", "_node_status", "_sub_node_properties")

    def __init__(self, app=None) -> None:
        self._app = app
        self._sub_node_config: Config | None = None
        self._sub_node_command: SubNodeCommand | None = None
        self._node_status: NodeStatus = NodeStatus(None)
        self._sub_node_properties: SubNodeProperties | None = None

    # deprecated
    @classmethod
    def from_dict(cls, d: dict, app=None) -> SubNode:
        return cls(app=app)

    # -----------------------------------------------------------------------
    # Node facade
    # -----------------------------------------------------------------------

    @property
    def sub_node_command_(self) -> SubNodeCommand:
        if self._sub_node_command is None:
            self._sub_node_command = SubNodeCommand(self._app)
        return self._sub_node_command

    @property
    def sub_node_properties_(self) -> SubNodeProperties:
        if self._sub_node_properties is None:
            self._sub_node_properties = SubNodeProperties(self._app)
        return self._sub_node_properties

    @property
    def node_status_(self) -> NodeStatus:
        return self._node_status

    @property
    def status_(self) -> Status | None:
        return self._node_status.status_

    @property
    def is_ready_(self) -> bool:
        return self._node_status.is_ready_

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def node_name_(self) -> str:
        return self.sub_node_properties_.sub_node_name_

    @property
    def mode_(self) -> str | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('role')

    @property
    def model_(self) -> str | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('model')

    @property
    def timeout_(self) -> int | None:
        if self._sub_node_config is None:
            return None
        return self._sub_node_config.config_dict_.get('timeout')

    @property
    def entrypoint_path_(self) -> PathType:
        path = Path.new(self._sub_node_config.config_dict_['runner_root_dir']).resolve() / 'entrypoint.py'
        _assert_entrypoint_exists(path)
        return path.resolve()

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init_sub_node(
        self,
        sub_node_config_dict: dict,
        writer=None,
        reader=None,
    ) -> None:
        if writer is None:
            writer = default_write_utf8
        if reader is None:
            reader = default_read_utf8
        _init_sub_node(self, sub_node_config_dict, writer, reader)

    def init_sub_node_command(self, task_dir, python_exe=None) -> None:
        self.sub_node_command_.init_sub_node_command(
            self.sub_node_properties_,
            task_dir,
            python_exe,
        )

    def run_sub_node(self, task_dir, runner=None, python_exe=None) -> dict:
        return _run_sub_node(self, task_dir, self._app, runner=runner, python_exe=python_exe)
```

### platform/shell/structure/sub_node/sub_node_command/__init__.py
```
from shell.structure.sub_node.sub_node_command.sub_node_command import SubNodeCommand

__all__ = ["SubNodeCommand"]
```

### platform/shell/structure/sub_node/sub_node_command/internal/__init__.py
```

```

### platform/shell/structure/sub_node/sub_node_command/internal/_assert_model_set.py
```
def _assert_model_set(model) -> None:
    if not model:
        raise RuntimeError("[SubNodeCommand] model is not set — pass --model to the CLI")
```

### platform/shell/structure/sub_node/sub_node_command/internal/_assert_source_dir_set.py
```
from shell.utils.path.path import PathType


def _assert_source_dir_set(source_dir) -> None:
    if not source_dir:
        raise RuntimeError("[SubNodeCommand] source_dir is not set — pass --source-dir to the CLI")
```

### platform/shell/structure/sub_node/sub_node_command/internal/_assert_sub_node_command_set.py
```
def _assert_sub_node_command_set(command) -> None:
    if command is None:
        raise ValueError("[SubNodeCommand] _command is not set — call init_sub_node_command() first")
```

### platform/shell/structure/sub_node/sub_node_command/internal/_assert_task_dir_set.py
```
def _assert_task_dir_set(task_dir) -> None:
    if not task_dir:
        raise RuntimeError("[SubNodeCommand] task_dir is not set — pass --task-dir to the CLI")
```

### platform/shell/structure/sub_node/sub_node_command/internal/_assert_task_name_set.py
```
def _assert_task_name_set(task_name) -> None:
    if not task_name:
        raise RuntimeError("[SubNodeCommand] task_name is not set — pass --task-name to the CLI")
```

### platform/shell/structure/sub_node/sub_node_command/internal/_assert_work_dir_set.py
```
def _assert_work_dir_set(work_dir) -> None:
    if not work_dir:
        raise RuntimeError("[SubNodeCommand] work_dir is not set — pass --work-dir to the CLI")
```

### platform/shell/structure/sub_node/sub_node_command/internal/_init_sub_node_command.py
```
from shell.utils.path.path import Path, PathType
import sys


from shell.structure.sub_node.sub_node.internal._assert_entrypoint_exists import _assert_entrypoint_exists
from shell.structure.sub_node.sub_node_command.internal._assert_source_dir_set import _assert_source_dir_set
from shell.structure.sub_node.sub_node_command.internal._assert_task_dir_set import _assert_task_dir_set
from shell.structure.sub_node.sub_node_command.internal._assert_task_name_set import _assert_task_name_set
from shell.structure.sub_node.sub_node_command.internal._assert_work_dir_set import _assert_work_dir_set
from shell.structure.sub_node.sub_node_command.internal._assert_model_set import _assert_model_set


def _init_sub_node_command(sub_node_command, sub_node_properties, task_dir, python_exe=None) -> None:
    if python_exe is None:
        python_exe = sys.executable

    app = sub_node_command._app
    node_name = sub_node_properties.sub_node_name_
    parent_node_dir = sub_node_properties.parent_node_dir_
    runner_root_dir = sub_node_properties.sub_node_runner_root_dir_
    mode = sub_node_properties.mode_
    model = sub_node_properties.model_
    cli = app.cli_
    task_name = sub_node_properties.task_name_ or cli.task_name_
    source_dir = sub_node_properties.source_dir_ or cli.source_dir_
    work_dir = sub_node_properties.work_dir_ or cli.work_dir_
    thread_id = cli.thread_id_
    _assert_source_dir_set(source_dir)
    _assert_work_dir_set(work_dir)
    _assert_task_name_set(task_name)
    _assert_task_dir_set(task_dir)

    node_dir = Path.new(parent_node_dir) / node_name
    entrypoint_path = Path.new(runner_root_dir).resolve() / 'entrypoint.py'
    _assert_entrypoint_exists(entrypoint_path)

    sub_node_command.command_.extend_command_args([python_exe, str(entrypoint_path)])
    sub_node_command.command_.extend_command_args(['--node-dir', str(node_dir)])
    sub_node_command.command_.extend_command_args(['--source-dir', str(source_dir)])
    sub_node_command.command_.extend_command_args(['--work-dir', str(work_dir)])
    sub_node_command.command_.extend_command_args(['--task-name', task_name])
    sub_node_command.command_.extend_command_args(['--task-dir', str(task_dir)])

    if parent_node_dir is not None:
        sub_node_command.command_.extend_command_args(['--parent-node-dir', str(parent_node_dir)])
        app.app_trace_.record_info('sub_node_command._init_sub_node_command', f'parent_node_dir set: {parent_node_dir}')
    else:
        app.app_trace_.record_info('sub_node_command._init_sub_node_command', 'parent_node_dir not set')

    if thread_id is not None:
        sub_node_command.command_.extend_command_args(['--parent-thread-id', thread_id])

    if mode == 'agent':
        _assert_model_set(model)
        sub_node_command.command_.extend_command_args(['--model', model])

    role = sub_node_properties.role_
    if role is not None:
        sub_node_command.command_.extend_command_args(['--role', role])

    timeout = sub_node_properties.timeout_
    if timeout is not None:
        sub_node_command.command_.extend_command_args(['--timeout', str(timeout)])

```

### platform/shell/structure/sub_node/sub_node_command/sub_node_command.py
```
"""sub_node_command.py
SubNodeCommand — builds and holds the subprocess command for a graph node.

Slots:
    _app     — parent App
    _command — built command list (list[str] | None)
"""

from __future__ import annotations

from shell.structure.sub_node.sub_node_command.internal._assert_sub_node_command_set import _assert_sub_node_command_set
from shell.structure.sub_node.sub_node_command.internal._init_sub_node_command import _init_sub_node_command
from shell.component.command.command import Command


class SubNodeCommand:
    """Builds and holds the subprocess command for a single graph node."""

    __slots__ = ("_app", "_command",)

    def __init__(self, app=None) -> None:
        self._app = app
        self._command: Command | None = None

    @property
    def command_(self) -> Command:
        _assert_sub_node_command_set(self._command)
        return self._command

    def init_sub_node_command(self, sub_node_configuration, task_dir, python_exe=None) -> None:
        _init_sub_node_command(self, sub_node_configuration, task_dir, python_exe)
```

### platform/shell/structure/sub_node/sub_node_properties/__init__.py
```
from shell.structure.sub_node.sub_node_properties.sub_node_properties import SubNodeProperties
```

### platform/shell/structure/sub_node/sub_node_properties/internal/__init__.py
```
```

### platform/shell/structure/sub_node/sub_node_properties/internal/_assert_sub_node_properties_loaded.py
```
def _assert_sub_node_properties_loaded(name: str | None) -> None:
    if name is None:
        raise ValueError("[SubNodeProperties] not loaded — call init_sub_node_properties() first")
```

### platform/shell/structure/sub_node/sub_node_properties/internal/_init_sub_node_properties.py
```
from __future__ import annotations

from shell.structure.node.node.internal._validate_node import _validate_node


def _init_sub_node_properties(sub_node_properties, sub_node_config_dict: dict, writer=None) -> None:
    sub_node_properties.sub_node_dir_ = sub_node_config_dict['sub_node_dir']
    sub_node_properties.sub_node_runner_root_dir_ = sub_node_config_dict.get('runner_root_dir')
    node_dir = sub_node_properties.node_dir_
    runner_root_dir = sub_node_config_dict['runner_root_dir']
    sub_node_properties.sub_node_node_config_.append_node_config(node_dir, sub_node_config_dict, runner_root_dir, overwrite=True, writer=writer)
    _validate_node(node_dir)
    config_dict = sub_node_properties.sub_node_node_config_.config_.config_dict_
    sub_node_properties._name = config_dict.get('name')
    sub_node_properties._mode = config_dict.get('mode')
    sub_node_properties._role = config_dict.get('role')
    sub_node_properties._type = config_dict.get('type')
    sub_node_properties._model = config_dict.get('model')
    sub_node_properties._command = config_dict.get('command')
    sub_node_properties._timeout = config_dict.get('timeout')
    sub_node_properties._retries = config_dict.get('retries')
    sub_node_properties._log_level = config_dict.get('log_level')
    sub_node_properties._max_step = config_dict.get('max_step')
    sub_node_properties._no_ask_user = config_dict.get('no_ask_user')
    sub_node_properties._autopilot = config_dict.get('autopilot')
    sub_node_properties._task_name = config_dict.get('task_name')
    sub_node_properties._source_dir = config_dict.get('source_dir')
    sub_node_properties._work_dir = config_dict.get('work_dir')
```

### platform/shell/structure/sub_node/sub_node_properties/sub_node_properties.py
```
"""sub_node_properties.py
SubNodeProperties — parsed attributes of a sub_node's config.yaml,
with node infrastructure slots migrated from SubNodeConfiguration.

Slots:
    _app                      — parent App (DOM back-reference)
    _sub_node                 — parent SubNode back-reference (Optional)
    _sub_node_dir             — raw path string to the node directory (str | None)
    _sub_node_name            — node name (str | None)
    _sub_node_runner_root_dir — path to the runner root directory (str | None)
    _sub_node_node_config     — lazy NodeConfig instance
    _sub_node_node_stage      — lazy NodeStage instance
    _name        — node name identifier
    _mode        — node mode (agent | router | worker | tool | tasker)
    _role        — logical role of the node
    _type        — type identifier of the node
    _model       — Optional; LLM model name
    _command     — Optional; path to the CLI binary
    _timeout     — Optional; LLM call timeout in seconds
    _retries     — Optional; number of retries on failure
    _log_level   — Optional; log level (INFO, DEBUG, etc.)
    _max_step    — Optional; maximum TTL step
    _no_ask_user — Optional; if True, non-interactive mode
    _autopilot   — Optional; if True, no confirmation prompts
    _task_name   — Optional; task name for mode: tasker nodes
    _source_dir  — Optional; source directory
    _work_dir    — Optional; shared workspace directory
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.structure.node.node_config.node_config import NodeConfig
from shell.structure.node.node_stage.node_stage import NodeStage
from shell.structure.sub_node.sub_node_properties.internal._assert_sub_node_properties_loaded import _assert_sub_node_properties_loaded
from shell.structure.sub_node.sub_node_properties.internal._init_sub_node_properties import _init_sub_node_properties


class SubNodeProperties:
    __slots__ = (
        "_app",
        "_sub_node",
        "_sub_node_dir",
        "_sub_node_name",
        "_sub_node_runner_root_dir",
        "_sub_node_node_config",
        "_sub_node_node_stage",
        "_name",
        "_mode",
        "_role",
        "_type",
        "_model",
        "_command",
        "_timeout",
        "_retries",
        "_log_level",
        "_max_step",
        "_no_ask_user",
        "_autopilot",
        "_task_name",
        "_source_dir",
        "_work_dir",
    )

    def __init__(self, app=None) -> None:
        self._app = app
        self._sub_node = None
        self._sub_node_dir: str | None = None
        self._sub_node_name: str | None = None
        self._sub_node_runner_root_dir: str | None = None
        self._sub_node_node_config = None
        self._sub_node_node_stage = None
        self._name: str | None = None
        self._mode: str | None = None
        self._role: str | None = None
        self._type: str | None = None
        self._model: str | None = None
        self._command: str | None = None
        self._timeout: int | None = None
        self._retries: int | None = None
        self._log_level: str | None = None
        self._max_step: int | None = None
        self._no_ask_user: bool | None = None
        self._autopilot: bool | None = None
        self._task_name: str | None = None
        self._source_dir: str | None = None
        self._work_dir: str | None = None

    @property
    def node_dir_(self) -> PathType:
        from shell.structure.node.node.internal._assert_node_dir_set import _assert_node_dir_set
        _assert_node_dir_set(self._sub_node_dir)
        return Path.new(self._sub_node_dir).resolve()

    @property
    def sub_node_dir_(self) -> str | None:
        return self._sub_node_dir

    @sub_node_dir_.setter
    def sub_node_dir_(self, value: str) -> None:
        self._sub_node_dir = value
        self._sub_node_name = Path.new(value).name

    @property
    def sub_node_name_(self) -> str:
        return self._sub_node_name if self._sub_node_name else self.node_dir_.name

    @property
    def parent_node_dir_(self) -> str | None:
        return str(Path.new(self._sub_node_dir).parent) if self._sub_node_dir else None

    @property
    def sub_node_runner_root_dir_(self) -> str | None:
        return self._sub_node_runner_root_dir

    @sub_node_runner_root_dir_.setter
    def sub_node_runner_root_dir_(self, value: str | None) -> None:
        self._sub_node_runner_root_dir = value

    @property
    def sub_node_node_config_(self) -> NodeConfig:
        if self._sub_node_node_config is None:
            self._sub_node_node_config = NodeConfig(self._app)
        return self._sub_node_node_config

    @property
    def sub_node_node_stage_(self) -> NodeStage:
        if self._sub_node_node_stage is None:
            self._sub_node_node_stage = NodeStage(self._app)
        return self._sub_node_node_stage

    @property
    def name_(self) -> str:
        _assert_sub_node_properties_loaded(self._name)
        return self._name

    @property
    def mode_(self) -> str | None:
        return self._mode

    @property
    def role_(self) -> str | None:
        return self._role

    @property
    def type_(self) -> str | None:
        return self._type

    @property
    def model_(self) -> str | None:
        return self._model

    @property
    def command_(self) -> str | None:
        return self._command

    @property
    def timeout_(self) -> int | None:
        return self._timeout

    @property
    def retries_(self) -> int | None:
        return self._retries

    @property
    def log_level_(self) -> str | None:
        return self._log_level

    @property
    def max_step_(self) -> int | None:
        return self._max_step

    @property
    def no_ask_user_(self) -> bool | None:
        return self._no_ask_user

    @property
    def autopilot_(self) -> bool | None:
        return self._autopilot

    @property
    def task_name_(self) -> str | None:
        return self._task_name

    @property
    def source_dir_(self) -> str | None:
        return self._source_dir

    @property
    def work_dir_(self) -> str | None:
        return self._work_dir

    def init_sub_node_properties(self, sub_node_config_dict: dict, writer=None) -> None:
        _init_sub_node_properties(self, sub_node_config_dict, writer=writer)
```

### platform/shell/utils/__init__.py
```
```

### platform/shell/utils/file/__init__.py
```
# lib/data package
```

### platform/shell/utils/file/File.py
```
"""File.py
File — DOM node representing a single file on disk.

Fields:
    _file_path  — absolute path to the file
    _file_body  — cached file content (str)

Properties:
    file_body_  — validated file content, raises ValueError if not loaded
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.utils.file.internal._assert_file_loaded import _assert_file_loaded
from shell.utils.file.internal._read_file import _read_file
from shell.utils.file.internal._save_file import _save_file


class File:
    """DOM node for a single file on disk."""

    __slots__ = ("_file_path", "_file_body")

    def __init__(self, path: str | PathType) -> None:
        self._file_path: PathType = Path.new(path)
        self._file_body: str = ""

    @property
    def file_body_(self) -> str:
        """Return file content. Raises ValueError if not yet loaded."""
        _assert_file_loaded(self._file_body, self._file_path)
        return self._file_body

    def read_file(self, encoding: str = "utf-8") -> None:
        """Read file from disk into _file_body.

        Raises ValueError for unsupported file types.
        Raises OSError if file cannot be read.
        """
        self._file_body = _read_file(self._file_path, encoding)

    def save_file(self, encoding: str = "utf-8") -> None:
        """Write _file_body to disk.

        Raises ValueError if file_body is empty or file type is unsupported.
        """
        _save_file(self._file_path, self._file_body, encoding)
```

### platform/shell/utils/file/internal/__init__.py
```
# file internal package
```

### platform/shell/utils/file/internal/_assert_file_body_not_empty.py
```
"""_assert_file_body_not_empty.py
Validate that file_body is not empty.
"""

from __future__ import annotations


def _assert_file_body_not_empty(file_body: str) -> None:
    """Raise ValueError if file_body is empty."""
    if not file_body:
        raise ValueError("Cannot save empty file_body.")
```

### platform/shell/utils/file/internal/_assert_file_loaded.py
```
"""_assert_file_loaded.py
Validate that file has been loaded (file_body is not empty).
"""

from __future__ import annotations

from shell.utils.path.path import PathType




def _assert_file_loaded(file_body: str, file_path: PathType) -> None:
    """Raise ValueError if file_body is empty (file not yet loaded)."""
    if not file_body:
        raise ValueError(f"File not loaded: {file_path}")
```

### platform/shell/utils/file/internal/_assert_suffix_allowed.py
```
"""_assert_suffix_allowed.py
Validate that a file suffix is in the allowed set.
"""

from __future__ import annotations

from shell.utils.path.path import PathType



_ALLOWED_SUFFIXES: frozenset[str] = frozenset({
    ".md", ".txt", ".yaml", ".yml", ".json", ".log",
})


def _assert_suffix_allowed(file_path: PathType) -> None:
    """Raise ValueError if file_path suffix is not in _ALLOWED_SUFFIXES."""
    if file_path.suffix.lower() not in _ALLOWED_SUFFIXES:
        raise ValueError(
            f"Unsupported file type: '{file_path.suffix}'. "
            f"Allowed: {sorted(_ALLOWED_SUFFIXES)}"
        )
```

### platform/shell/utils/file/internal/_read_file.py
```
from __future__ import annotations


from shell.utils.file.internal._assert_suffix_allowed import _assert_suffix_allowed
from shell.utils.path.path import Path, PathType


def _read_file(file_path: PathType, encoding: str = "utf-8") -> str:
    _assert_suffix_allowed(file_path)
    return Path.read_text(file_path)
```

### platform/shell/utils/file/internal/_save_file.py
```
from __future__ import annotations


from shell.utils.file.internal._assert_file_body_not_empty import _assert_file_body_not_empty
from shell.utils.file.internal._assert_suffix_allowed import _assert_suffix_allowed
from shell.utils.path.path import Path, PathType


def _save_file(file_path: PathType, file_body: str, encoding: str = "utf-8") -> None:
    _assert_file_body_not_empty(file_body)
    _assert_suffix_allowed(file_path)
    Path.mkdir(file_path.parent)
    Path.write_text(file_path, file_body)
```

### platform/shell/utils/io/__init__.py
```
```

### platform/shell/utils/io/io.py
```
from __future__ import annotations

import logging

from shell.utils.path.path import Path


def default_read_utf8(path) -> str:
    return Path.read_text(path)


def default_read_utf8_safe(path) -> str:
    return Path.read_text_safe(path)


def default_write_utf8(path, text: str) -> None:
    Path.write_text(path, text)


def default_make_dirs(path) -> None:
    Path.mkdir(path)


def default_unlink(path) -> None:
    Path.unlink(path)


def default_file_handler(path) -> logging.FileHandler:
    return logging.FileHandler(path, encoding="utf-8")
```

### platform/shell/utils/path/__init__.py
```
```

### platform/shell/utils/path/path.py
```
"""path.py
Path — static proxy for file and directory operations on a pathlib.Path.
"""

from __future__ import annotations

import shutil
from pathlib import Path as _Path


PathType = _Path


class Path:
    """Static proxy for file and directory operations on a pathlib.Path."""

    @staticmethod
    def new(*args) -> _Path:
        return _Path(*args)

    @staticmethod
    def mkdir(path: PathType) -> None:
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def exists(path: PathType) -> bool:
        return path.exists()

    @staticmethod
    def is_file(path: PathType) -> bool:
        return path.is_file()

    @staticmethod
    def is_dir(path: PathType) -> bool:
        return path.is_dir()

    @staticmethod
    def read_text(path: PathType) -> str:
        return path.read_text(encoding='utf-8')

    @staticmethod
    def write_text(path: PathType, text: str) -> None:
        path.write_text(text, encoding='utf-8')

    @staticmethod
    def unlink(path: PathType) -> None:
        path.unlink()

    @staticmethod
    def rmtree(path: PathType) -> None:
        shutil.rmtree(path)

    @staticmethod
    def copy_to(src: PathType, dest: PathType) -> None:
        shutil.copy2(src, dest)

    @staticmethod
    def move(src: PathType, dest: PathType) -> None:
        shutil.move(str(src), str(dest))

    @staticmethod
    def is_symlink(path: PathType) -> bool:
        return path.is_symlink()

    @staticmethod
    def iterdir(path: PathType) -> list[PathType]:
        return list(path.iterdir())

    @staticmethod
    def glob(path: PathType, pattern: str) -> list[PathType]:
        return sorted(path.glob(pattern))

    @staticmethod
    def rglob(path: PathType, pattern: str) -> list[PathType]:
        return sorted(path.rglob(pattern))

    @staticmethod
    def read_text_safe(path: PathType) -> str:
        return path.read_text(encoding='utf-8', errors='replace')
```

### platform/shell/utils/system/__init__.py
```
```

### platform/shell/utils/system/system.py
```
"""python_version_validator.py
Responsible for one thing: validating the Python interpreter version.
"""


class System:
    """Validates that the Python interpreter meets the minimum version requirement."""

    _MIN_VERSION = (3, 10)

    def validate(self, version_info=None):
        import sys
        version_info = version_info or sys.version_info

        if version_info < self._MIN_VERSION:
            raise RuntimeError(
                f"Python {self._MIN_VERSION[0]}.{self._MIN_VERSION[1]}+ required, "
                f"got {version_info[0]}.{version_info[1]}"
            )
```

### platform/temp/check_var_names.py
```
﻿"""check_var_names.py
Finds assignments where local variable name differs from the property name being assigned.
Example bad:  target = node_logs.logs_dir_   (should be: logs_dir = node_logs.logs_dir_)
"""
from __future__ import annotations

from shell.utils.path.path import Path, PathType
import re

base = Path.new(__file__).parent.parent / "shell"
prop_assign = re.compile(r'^\s*(\w+)\s*=\s*[\w.]+\.(\w+)_\s*$')

mismatches = []

for py_file in sorted(base.rglob("*.py")):
    try:
        lines = py_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    for lineno, line in enumerate(lines, 1):
        m = prop_assign.match(line)
        if not m:
            continue
        local_var = m.group(1)
        prop_base = m.group(2)
        if local_var in ("self", "cls", "return"):
            continue
        if local_var != prop_base:
            rel = py_file.relative_to(base)
            mismatches.append((str(rel), lineno, local_var, prop_base, line.strip()))

print(f"Total mismatches: {len(mismatches)}\n")
for rel, lineno, var, prop, line in mismatches:
    print(f"{rel}:{lineno}  |  {var!r} -> should be {prop!r}  |  {line}")
```

### platform/temp/list_slots.py
```
﻿"""list_slots.py
Skanuje pliki .py w podanym katalogu, zbiera wszystkie klasy z __slots__
i generuje posortowany plik class_slots.md (class_name, slot_name).

Użycie:
    python utils/list_slots.py [katalog] [--out PLIK]

Domyślnie skanuje platform/shell i zapisuje do utils/class_slots.md.

Przykłady:
    python utils/list_slots.py
    python utils/list_slots.py platform/shell --out utils/class_slots.md
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
import ast
import argparse
import sys


def collect_slots(root: PathType) -> list[tuple[str, str]]:
    rows = []
    for path in sorted(root.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.Assign):
                    continue
                for target in item.targets:
                    if not (isinstance(target, ast.Name) and target.id == "__slots__"):
                        continue
                    slots = _extract_slots(item.value)
                    for slot in slots:
                        rows.append((node.name, slot))
    return sorted(rows, key=lambda r: (r[0].lower(), r[1].lower()))


def _extract_slots(node: ast.expr) -> list[str]:
    if isinstance(node, (ast.Tuple, ast.List)):
        return [elt.value for elt in node.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def write_md(rows: list[tuple[str, str]], out: PathType) -> None:
    lines = ["# class_slots\n", "\n", "| class_name | slot_name |\n", "|---|---|\n"]
    for class_name, slot_name in rows:
        lines.append(f"| {class_name} | {slot_name} |\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines), encoding="utf-8")
    print(f"Zapisano {len(rows)} wierszy do {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generuje class_slots.md ze __slots__ w kodzie Python.")
    parser.add_argument("directory", nargs="?", default="platform/shell", help="Katalog do skanowania")
    parser.add_argument("--out", default="utils/class_slots.md", help="Plik wyjściowy")
    args = parser.parse_args()

    project_root = Path.new(__file__).parent.parent
    scan_dir = project_root / args.directory
    out_file = project_root / args.out

    if not scan_dir.exists():
        print(f"Błąd: katalog '{scan_dir}' nie istnieje.", file=sys.stderr)
        sys.exit(1)

    rows = collect_slots(scan_dir)
    write_md(rows, out_file)


if __name__ == "__main__":
    main()
```

### platform/temp/nodechild_lazy_loading_and_init_andproperty_algoritm.md
```
﻿# NodeLogs — wzorzec lazy loading, inicjalizacja, konstruktor, property, sloty

## Sloty

```python
__slots__ = ("_app", "_module_status")
```

- `_app` — referencja do parent App; przekazywana przez konstruktor
- `_module_status` — enum `ModuleStatus` (z `shell.module_status.module_status`); ustawiany w konstruktorze na `NEW`, zmieniany na `INIT` przez `init_node_logs()`

---

## Konstruktor

Konstruktor **tylko zeruje sloty** — bez logiki inicjalizacyjnej, bez tworzenia katalogów.

```python
def __init__(self, app) -> None:
    self._app = app
    self._module_status: ModuleStatus = ModuleStatus.NEW
```

- `app` — jedyny parametr; ścieżka **nie jest** przekazywana do konstruktora
- ścieżka `logs_dir` budowana jest **lazy w property** przez `_app`

---

## Property

### Ścieżka — budowana przez `_app`, nie slot

```python
@property
def node_logs_dir_(self) -> Path:
    return (self._app.app_node_.node_.node_dir_ / '.node' / 'logs').resolve()
```

Ścieżka nie jest trzymana jako slot — pobierana dynamicznie przez łańcuch `_app → app_node_ → node_ → node_dir_`.

### Status

```python
@property
def module_status_(self) -> ModuleStatus:
    return self._module_status
```

---

## Metoda inicjalizacyjna

```python
def init_node_logs(self) -> None:
    self._module_status = ModuleStatus.INIT
```

Wywoływana z `_init_node(node, ...)` po `node.node_input_.init_input()`.

---

## Lazy loading w klasie Node

```python
@property
def node_logs_(self) -> NodeLogs:
    if self._node_logs is None:
        self._node_logs = NodeLogs(self._app)
    return self._node_logs
```

- slot w `Node.__slots__`: `"_node_logs"`
- inicjalizacja w `__init__`: `self._node_logs = None  # NodeLogs, lazy`
- do konstruktora przekazywany **tylko `self._app`**, bez ścieżki

---

## Wywołanie init w `_init_node`

```python
node.node_input_.init_input()
node.node_logs_.init_node_logs()
```
```

### platform/tests/agent/__init__.py
```

```

### platform/tests/agent/internal/__init__.py
```

```

### platform/tests/app/__init__.py
```

```

### platform/tests/app/internal/__init__.py
```

```

### platform/tests/cli/__init__.py
```

```

### platform/tests/cli/internal/__init__.py
```

```

### platform/tests/cli/internal/test__parse_args.py
```
﻿"""Tests for lib/args/_parse_args.py

Verifies that raw CLI argument parsing produces the correct Namespace values.
"""

import pytest
from shell.component.cli.cli.internal._parse_args import _parse_args


def test_no_args_produces_safe_defaults():
    ns = _parse_args([])
    assert ns.node_dir is None
    assert ns.version is False
    assert ns.clean is False
    assert ns.clean_out is False
    assert ns.dry_run is False
    assert ns.log_level is None
    assert ns.no_ask_user is False
    assert ns.autopilot is False
    assert ns.add_dirs == []
    assert ns.prompt is None


def test_node_flag_is_captured():
    ns = _parse_args(["--node-dir", "/some/path"])
    assert ns.node_dir == "/some/path"


def test_boolean_flags_are_set():
    ns = _parse_args(["--version", "--clean", "--dry-run", "--no-ask-user", "--autopilot"])
    assert ns.version is True
    assert ns.clean is True
    assert ns.dry_run is True
    assert ns.no_ask_user is True
    assert ns.autopilot is True


def test_log_level_is_captured():
    ns = _parse_args(["--log-level", "DEBUG"])
    assert ns.log_level == "DEBUG"


def test_add_dir_accumulates_multiple_values():
    ns = _parse_args(["--add-dir", "/a", "--add-dir", "/b"])
    assert ns.add_dirs == ["/a", "/b"]


def test_prompt_flag_is_captured():
    ns = _parse_args(["--prompt", "do the thing"])
    assert ns.prompt == "do the thing"


def test_clean_out_flag():
    ns = _parse_args(["--clean-out"])
    assert ns.clean_out is True
```

### platform/tests/cli/internal/test__prepare_args.py
```
﻿from shell.utils.path.path import PathType
from shell.app.app import App
from shell.component.cli.cli.internal._init_cli import _init_cli


def test_node_flag_is_written_to_config(tmp_path):
    node_dir = tmp_path / "my_node"
    node_dir.mkdir()
    app = App()
    _init_cli(app.app_config_.cli_, argv=["--node-dir", str(node_dir)])
    assert app.app_config_.cli_.cli_properties_._node_dir == str(node_dir)


def test_source_dir_is_set_from_flag(tmp_path):
    app = App()
    _init_cli(app.app_config_.cli_, argv=["--source-dir", str(tmp_path)])
    assert app.app_config_.cli_.cli_properties_._source_dir == str(tmp_path)

```

### platform/tests/cli/internal/test__validate_args.py
```
﻿import pytest
from shell.component.cli.cli.internal._assert_node_dir_set import _assert_node_dir_set
from shell.component.cli.cli.internal._assert_task_name_set import _assert_task_name_set
from shell.component.cli.cli.internal._assert_mode_allowed import _assert_mode_allowed


def test_assert_node_dir_set_raises_in_agent_mode_when_missing():
    with pytest.raises(ValueError, match="--node-dir"):
        _assert_node_dir_set(None, 'agent')


def test_assert_node_dir_set_does_not_raise_when_present():
    _assert_node_dir_set("/some/path", 'agent')


def test_assert_node_dir_set_does_not_raise_when_mode_none():
    _assert_node_dir_set(None, None)


def test_assert_task_name_set_raises_in_tasker_mode_when_missing():
    with pytest.raises(ValueError, match="--task-name"):
        _assert_task_name_set(None, 'tasker')


def test_assert_task_name_set_does_not_raise_when_present():
    _assert_task_name_set("my-task", 'tasker')


def test_assert_mode_allowed_raises_for_unknown_mode():
    with pytest.raises(ValueError, match="mode is required"):
        _assert_mode_allowed('unknown')


def test_assert_mode_allowed_does_not_raise_for_agent():
    _assert_mode_allowed('agent')


def test_assert_mode_allowed_does_not_raise_for_tasker():
    _assert_mode_allowed('tasker')
```

### platform/tests/conftest.py
```
﻿from shell.utils.path.path import Path, PathType
import sys
import logging

import pytest

from shell.app.app import App

# Make the shared `lib` package (outside this package) importable in tests.
_LIB_ROOT = Path.new(__file__).resolve().parents[2]  # 07-automation/
if str(_LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIB_ROOT))


@pytest.fixture
def fake_logger():
    """Logger writing nowhere — prevents any log file creation during tests."""
    logger = logging.getLogger("worker2-test")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


@pytest.fixture
def cfg(fake_logger):
    """Minimal app with pre-injected logger to avoid filesystem side effects."""
    cfg = App(logger=fake_logger)
    return cfg


@pytest.fixture
def node_dir(tmp_path):
    """Minimal valid node directory structure."""
    (tmp_path / '.node' / 'app').mkdir(parents=True)
    (tmp_path / '.node' / 'app' / 'app.yaml').write_text('# app\n', encoding='utf-8')
    (tmp_path / 'input').mkdir()
    (tmp_path / 'output').mkdir()
    (tmp_path / 'archive').mkdir()
    return tmp_path


@pytest.fixture
def cfg_with_node(cfg, node_dir):
    """App with pre-injected logger and a real valid node directory."""
    cfg.app_node_.node_._node_dir = str(node_dir)
    return cfg
```

### platform/tests/execute/__init__.py
```

```

### platform/tests/graph/__init__.py
```

```

### platform/tests/graph_node/__init__.py
```

```

### platform/tests/graph_node/internal/__init__.py
```

```

### platform/tests/logger/__init__.py
```

```

### platform/tests/logger/internal/__init__.py
```

```

### platform/tests/logger/internal/test_logger_internals.py
```
﻿from shell.utils.path.path import PathType
"""Tests for lib/logger/_build_log_path.py and lib/logger/_get_logging_formatter.py

Verifies: correct log path construction, correct formatter pattern.
"""

import logging
import pytest
from datetime import datetime, timezone
from shell.logger.internal._build_log_path import _build_log_path
from shell.logger.internal._make_formatter import _make_formatter

_FIXED_NOW = datetime(2026, 4, 8, 15, 30, 0, tzinfo=timezone.utc)

# --- _build_log_path ---

def test_log_path_is_inside_node_logs_dir(tmp_path):
    log_path = _build_log_path(tmp_path, "INFO", now=_FIXED_NOW)
    assert log_path.parent == tmp_path / "logs"


def test_log_path_filename_contains_level(tmp_path):
    log_path = _build_log_path(tmp_path, "DEBUG", now=_FIXED_NOW)
    assert "debug" in log_path.name


def test_log_path_filename_contains_date(tmp_path):
    log_path = _build_log_path(tmp_path, "INFO", now=_FIXED_NOW)
    assert "2026-04-08" in log_path.name


def test_log_path_filename_contains_hour(tmp_path):
    log_path = _build_log_path(tmp_path, "INFO", now=_FIXED_NOW)
    assert "_15" in log_path.name


def test_log_path_filename_is_lowercase(tmp_path):
    log_path = _build_log_path(tmp_path, "WARNING", now=_FIXED_NOW)
    assert log_path.name == "agent.2026-04-08_15.warning.log"


def test_default_level_is_info(tmp_path):
    log_path = _build_log_path(tmp_path, now=_FIXED_NOW)
    assert "info" in log_path.name


# --- _make_formatter ---

def test_formatter_is_logging_formatter_instance():
    fmt = _make_formatter()
    assert isinstance(fmt, logging.Formatter)


def test_formatter_pattern_contains_levelname():
    fmt = _make_formatter()
    assert "levelname" in fmt._fmt


def test_formatter_pattern_contains_message():
    fmt = _make_formatter()
    assert "message" in fmt._fmt
```

### platform/tests/manifest/__init__.py
```

```

### platform/tests/manifest/internal/__init__.py
```

```

### platform/tests/node/__init__.py
```

```

### platform/tests/node/internal/__init__.py
```

```

### platform/tests/node/test_clean_node.py
```
﻿"""Tests for Node.clean_node()

Verifies: unlink called for files, rmtree called for subdirectories,
missing directories are skipped, OSError on individual items is ignored.
"""

import pytest
from shell.app.app import App

_CLEAN_DIRS = ("tmp", "script")


def _make_node_with_content(tmp_path):
    """Create a node with files and subdirs in all cleanable dirs."""
    for dir_name in _CLEAN_DIRS:
        d = tmp_path / dir_name
        d.mkdir(exist_ok=True)
        (d / "file.txt").write_text("content")
        (d / "subdir").mkdir()
    return tmp_path


def test_unlink_called_for_files_in_cleanable_dirs(cfg_with_node, node_dir):
    _make_node_with_content(node_dir)
    unlinked = []
    rmtrees = []
    cfg_with_node.app_node_.node_.clean_node(rmtree=rmtrees.append, unlink=unlinked.append)
    # Each cleanable dir has one file
    assert len(unlinked) >= len(_CLEAN_DIRS)


def test_rmtree_called_for_subdirectories_in_cleanable_dirs(cfg_with_node, node_dir):
    _make_node_with_content(node_dir)
    rmtrees = []
    cfg_with_node.app_node_.node_.clean_node(rmtree=rmtrees.append, unlink=lambda p: None)
    # Each cleanable dir has one subdir
    assert len(rmtrees) >= len(_CLEAN_DIRS)


def test_missing_cleanable_directory_is_skipped(cfg_with_node, node_dir):
    # Remove 'temp' if it exists; it's optional
    import shutil
    for d in ["temp"]:
        target = node_dir / d
        if target.exists():
            shutil.rmtree(target)
    # Must not raise
    cfg_with_node.app_node_.node_.clean_node(rmtree=lambda p: None, unlink=lambda p: None)


def test_oserror_on_item_is_silently_ignored(cfg_with_node, node_dir):
    (node_dir / "tmp").mkdir(exist_ok=True)
    (node_dir / "tmp" / "bad.txt").write_text("x")

    def raising_unlink(p):
        raise OSError("permission denied")

    # Must not propagate the OSError
    cfg_with_node.app_node_.node_.clean_node(rmtree=lambda p: None, unlink=raising_unlink)


def test_clean_node_uses_real_filesystem_by_default(node_dir):
    """Integration: verify real files are removed without DI."""
    import logging
    logger = logging.getLogger("test")
    logger.addHandler(logging.NullHandler())
    app = App(logger=logger)
    app.app_node_.node_._node_dir = str(node_dir)
    target = node_dir / "output" / "result.txt"
    target.write_text("output data")
    app.app_node_.node_.clean_node()
    assert not target.exists()
```

### platform/tests/prompt/__init__.py
```

```

### platform/tests/prompt/internal/__init__.py
```

```

### platform/tests/prompt/internal/test__resolve_prompt.py
```
﻿from shell.utils.path.path import PathType
"""Tests for shell/agent_prompt/internal/_resolve_prompt.py"""

import pytest
from shell.agent_prompt.internal._resolve_prompt import _resolve_prompt


def test_returns_file_content_for_existing_file_path(tmp_path):
    f = tmp_path / "custom.md"
    f.write_text("custom prompt text")
    result = _resolve_prompt(str(f), tmp_path, reader=lambda p: p.read_text())
    assert result == "custom prompt text"


def test_returns_directory_prompt_for_existing_directory_path(tmp_path):
    prompt_dir = tmp_path / "my_prompts"
    prompt_dir.mkdir()
    (prompt_dir / "0001_intro.md").write_text("Intro content")
    result = _resolve_prompt(str(prompt_dir), tmp_path, reader=lambda p: p.read_text())
    assert "Intro content" in result


def test_plain_text_is_returned_as_is(tmp_path):
    (tmp_path / "input").mkdir()
    (tmp_path / "temp").mkdir()
    result = _resolve_prompt("just plain text here", tmp_path)
    assert result == "just plain text here"


def test_simple_name_resolves_to_file_in_input(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "task.md").write_text("Task content")
    result = _resolve_prompt("task.md", tmp_path, reader=lambda p: p.read_text())
    assert result == "Task content"


def test_reader_is_used_for_file_reading(tmp_path):
    f = tmp_path / "p.md"
    f.write_text("original")
    result = _resolve_prompt(str(f), tmp_path, reader=lambda p: "injected content")
    assert result == "injected content"
```

### platform/tests/prompt/internal/test_build_from_dir_and_find_file.py
```
﻿from shell.utils.path.path import PathType
"""Tests for lib/llm_prompt/_build_from_dir.py and lib/llm_prompt/_find_file.py

_build_from_dir: builds structured Markdown from numbered section folders.
find_file: searches input/ then tmp/ for a file by name.
"""

import pytest
from shell.agent_prompt.internal._build_from_dir import _build_from_dir
from shell.agent_prompt.internal._find_file import _find_file


# --- build_from_dir ---

def test_returns_empty_string_for_empty_directory(tmp_path):
    result = _build_from_dir(tmp_path, reader=lambda f: "")
    assert result == ""


def test_builds_heading_from_file_stem(tmp_path):
    (tmp_path / "0001_context.md").write_text("Hello world")
    result = _build_from_dir(tmp_path, reader=lambda f: f.read_text())
    assert "# 1. Context" in result


def test_reader_is_called_for_each_file(tmp_path):
    (tmp_path / "0001_a.md").write_text("A")
    (tmp_path / "0002_b.md").write_text("B")
    seen = []
    def capturing_reader(f):
        seen.append(f.name)
        return ""
    _build_from_dir(tmp_path, reader=capturing_reader)
    assert "0001_a.md" in seen
    assert "0002_b.md" in seen


def test_numeric_prefix_removed_from_heading(tmp_path):
    (tmp_path / "0003_my_task.txt").write_text("content")
    result = _build_from_dir(tmp_path, reader=lambda f: "content")
    assert "0003" not in result
    assert "My task" in result


def test_files_are_ordered_by_name(tmp_path):
    (tmp_path / "0002_bbb.md").write_text("second")
    (tmp_path / "0001_aaa.md").write_text("first")
    result = _build_from_dir(tmp_path, reader=lambda f: f.read_text())
    assert result.index("# 1.") < result.index("# 2.")


# --- find_file ---

def test_find_file_locates_file_in_input(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "prompt.md").write_text("Hello")
    result = _find_file("prompt.md", tmp_path)
    assert result == input_dir / "prompt.md"


def test_find_file_locates_file_in_tmp_when_not_in_input(tmp_path):
    (tmp_path / "input").mkdir()
    tmp_dir = tmp_path / "temp"
    tmp_dir.mkdir()
    (tmp_dir / "context.txt").write_text("Context")
    result = _find_file("context.txt", tmp_path)
    assert result == tmp_dir / "context.txt"


def test_find_file_returns_none_when_not_found(tmp_path):
    (tmp_path / "input").mkdir()
    (tmp_path / "temp").mkdir()
    result = _find_file("missing.md", tmp_path)
    assert result is None


def test_find_file_prefers_input_over_tmp(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    tmp_dir = tmp_path / "temp"
    tmp_dir.mkdir()
    (input_dir / "target.md").write_text("from input")
    (tmp_dir / "target.md").write_text("from tmp")
    result = _find_file("target.md", tmp_path)
    assert result == input_dir / "target.md"
```

### platform/tests/router/__init__.py
```

```

### platform/tests/runner/__init__.py
```

```

### platform/tests/task/__init__.py
```

```

### platform/tests/task/internal/__init__.py
```

```

### platform/tests/task/test_task_and_execute.py
```
﻿from shell.utils.path.path import PathType
"""Tests for execute/runner modules:
execute_clean, execute_help, execute_version, app properties.
"""

import logging
import pytest
import yaml

from shell.app.app import App
from shell.component.manifest.manifest import Manifest


def _null_logger():
    logger = logging.getLogger("test-task-null")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# init_tasker
# ---------------------------------------------------------------------------

def test_init_tasker_copies_files_and_initializes_graph(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "my-task.md").write_text("# my-task\nsome task description", encoding="utf-8")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    graph_yaml = (
        "graph:\n"
        "  - node_name: agent-01\n"
        f"    parent_node_dir: {workspace_dir}\n"
        f"    runner_root_dir: {workspace_dir}\n"
        "    mode: agent\n"
        "    role: developer\n"
        "    type: agent\n"
        "    status: null\n"
    )
    (source_dir / "my-task.yaml").write_text(graph_yaml, encoding="utf-8")

    node_dir = tmp_path / "tasker-node"
    node_dir.mkdir()

    app = App(logger=_null_logger())
    app.app_node_.node_._node_dir = str(node_dir)
    app.app_config_.cli_.cli_properties_._task_name = "my-task"
    app.app_config_.cli_.cli_properties_._source_dir = str(source_dir)

    app.runner_.tasker_.init_tasker()

    task_dir = node_dir / ".node" / "task"
    assert (task_dir / "my-task.md").is_file()
    assert (task_dir / "graph_my-task.yaml").is_file()
    assert len(app.runner_.tasker_.graph_._graph_nodes) == 1



```

### platform/tests/throwable/__init__.py
```
```

### platform/utils/class_slots.md
```
﻿# class_slots

| class_name | slot_name |
|---|---|
| AgentProperties | _app |
| AgentProperties | _model |
| AgentProperties | _retries |
| AgentProperties | _retry_delay |
| AgentProperties | _timeout |
| App | _app_configuration |
| App | _app_node |
| App | _app_properties |
| App | _app_trace |
| App | _app_utils |
| App | _result |
| App | _runner |
| AppNode | _app |
| AppNode | _lock |
| AppNode | _node |
| AppProperties | _autopilot |
| AppProperties | _command |
| AppProperties | _log_level |
| AppProperties | _max_step |
| AppProperties | _mode |
| AppProperties | _model |
| AppProperties | _name |
| AppProperties | _no_ask_user |
| AppProperties | _retries |
| AppProperties | _role |
| AppProperties | _timeout |
| AppProperties | _type |
| AppUtils | _placeholders |
| Cli | _app |
| Cli | _cli_properties |
| CliProperties | _add_dirs |
| CliProperties | _allow_all_paths |
| CliProperties | _allow_all_tools |
| CliProperties | _autopilot |
| CliProperties | _clean |
| CliProperties | _clean_out |
| CliProperties | _prompt |
| CliProperties | _dry_run |
| CliProperties | _help |
| CliProperties | _log_level |
| CliProperties | _max_step |
| CliProperties | _mode |
| CliProperties | _model |
| CliProperties | _no_ask_user |
| CliProperties | _node_dir |
| CliProperties | _output_format |
| CliProperties | _parent_node_dir |
| CliProperties | _parent_thread_id |
| CliProperties | _prompt_dir |
| CliProperties | _role |
| CliProperties | _runner_root_dir |
| CliProperties | _source_dir |
| CliProperties | _step_number |
| CliProperties | _task_dir |
| CliProperties | _task_name |
| CliProperties | _thread_id |
| CliProperties | _timeout |
| CliProperties | _type |
| CliProperties | _version |
| CliProperties | _work_dir |
| Command | _command |
| Config | _app |
| Config | _config_dict |
| Config | _config_path |
| Event | _event_type |
| Event | _log_level_code |
| Event | _message |
| Event | _returncode |
| Event | _source |
| Event | _stderr |
| Event | _stdout |
| Event | _timestamp |
| File | _file_body |
| File | _file_path |
| FilePrompt | _file_body |
| FilePrompt | _file_name |
| FilePrompt | _prompt_type |
| Locker | _app |
| Locker | _lock_path |
| Logger | _app |
| Logger | _cached_logger |
| Logger | _log_level |
| Node | _app |
| Node | _node_archive |
| Node | _node_config |
| Node | _node_dir |
| Node | _node_input |
| Node | _node_logs |
| Node | _node_name |
| Node | _node_output |
| Node | _node_prompt |
| Node | _node_properties |
| Node | _node_scripts |
| Node | _node_stage |
| Node | _node_status |
| Node | _node_task |
| Node | _node_temp |
| NodeArchive | _app |
| NodeArchive | _module_status |
| NodeConfig | _app |
| NodeConfig | _module_status |
| NodeConfig | _node_config_file_body |
| NodeConfig | _node_properties |
| NodeLogs | _app |
| NodeLogs | _logs_dir |
| NodeLogs | _module_status |
| NodeOutput | _app |
| NodeOutput | _module_status |
| NodeOutput | _output_dir |
| NodeOutput | _output_files_map |
| NodePrompt | _app |
| NodePrompt | _module_status |
| NodePrompt | _prompt |
| NodePrompt | _prompt_dir |
| NodeScripts | _app |
| NodeScripts | _module_status |
| NodeScripts | _scripts_dir |
| NodeStage | _app |
| NodeStage | _module_status |
| NodeStage | _stage |
| NodeStage | _stage_dir |
| NodeStatus | _app |
| NodeStatus | _status |
| NodeTask | _app |
| NodeTask | _module_status |
| NodeTask | _task_md_file_body |
| NodeTask | _task_name |
| NodeTask | _task_yaml_file_body |
| NodeTemp | _app |
| NodeTemp | _module_status |
| NodeTemp | _temp_dir |
| Graph | _app |
| Graph | _status |
| Graph | _sub_nodes |
| Placeholders | _placeholder_list |
| Process | _process_command |
| Process | _returncode |
| Process | _runner |
| Process | _stderr |
| Process | _stdout |
| ProcessCommand | _command |
| Prompt | _app |
| Prompt | _file_prompts |
| Prompt | _prompt_cli |
| Prompt | _prompt_dir |
| Prompt | _prompt_input |
| Prompt | _prompt_role |
| Prompt | _prompt_skill |
| Prompt | _prompt_system |
| Prompt | _prompt_task |
| PromptCli | _app |
| PromptCli | _file_prompt |
| PromptInput | _app |
| PromptInput | _file_prompts |
| PromptRole | _app |
| PromptRole | _file_prompts |
| PromptSkill | _app |
| PromptSkill | _file_prompts |
| PromptSystem | _app |
| PromptSystem | _file_prompts |
| PromptTask | _app |
| PromptTask | _file_prompts |
| Result | _app |
| Result | _returncode |
| Result | _status |
| Result | _stderr |
| Result | _stdout |
| RouterBase | _app |
| RouterBase | _graph |
| RouterBase | _role_to_node_map |
| RouterStage | _app |
| RunnerProperties | _add_dirs |
| Stage | _app |
| Stage | _module_status |
| Stage | _stage_active |
| Stage | _stage_dead |
| Stage | _stage_dir |
| Stage | _stage_done |
| Stage | _stage_history |
| Stage | _stage_ignored |
| Stage | _stage_pending |
| StageActive | _active_dir |
| StageActive | _app |
| StageActive | _module_status |
| StageDead | _app |
| StageDead | _dead_dir |
| StageDead | _module_status |
| StageDone | _app |
| StageDone | _done_dir |
| StageDone | _module_status |
| StageHistory | _app |
| StageHistory | _history_dir |
| StageHistory | _module_status |
| StageIgnored | _app |
| StageIgnored | _ignored_dir |
| StageIgnored | _module_status |
| StagePending | _app |
| StagePending | _module_status |
| StagePending | _pending_dir |
| SubNode | _app |
| SubNode | _is_new |
| SubNode | _node_status |
| SubNode | _sub_node_command |
| SubNode | _sub_node_config_dict |
| SubNode | _sub_node_configuration |
| SubNode | _sub_node_properties |
| SubNodeCommand | _app |
| SubNodeCommand | _command |
| SubNodeConfiguration | _app |
| SubNodeConfiguration | _config |
| SubNodeConfiguration | _mode |
| SubNodeConfiguration | _model |
| SubNodeConfiguration | _node_archive |
| SubNodeConfiguration | _node_config |
| SubNodeConfiguration | _node_input |
| SubNodeConfiguration | _node_output |
| SubNodeConfiguration | _node_prompt |
| SubNodeConfiguration | _node_properties |
| SubNodeConfiguration | _node_stage |
| SubNodeConfiguration | _node_task |
| SubNodeConfiguration | _role |
| SubNodeConfiguration | _runner_root_dir |
| SubNodeConfiguration | _source_dir |
| SubNodeConfiguration | _sub_node |
| SubNodeConfiguration | _sub_node_dir |
| SubNodeConfiguration | _sub_node_name |
| SubNodeConfiguration | _task_name |
| SubNodeConfiguration | _timeout |
| SubNodeConfiguration | _type |
| SubNodeConfiguration | _work_dir |
| SubNodeProperties | _autopilot |
| SubNodeProperties | _command |
| SubNodeProperties | _log_level |
| SubNodeProperties | _max_step |
| SubNodeProperties | _mode |
| SubNodeProperties | _model |
| SubNodeProperties | _name |
| SubNodeProperties | _no_ask_user |
| SubNodeProperties | _retries |
| SubNodeProperties | _role |
| SubNodeProperties | _timeout |
| SubNodeProperties | _type |
| Tasker | _app |
| Tasker | _graph |
| Tasker | _session_id |
| Tool | _app |
| Tool | _tool_properties |
| ToolProperties | _app |
| Worker | _app |
| Worker | _script_file_body |
| Worker | _worker_properties |
| WorkerProperties | _app |
```

### router/default-router/config/config.yaml
```
name: default-router
mode: router
role: router
type: base
# Default configuration for router.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.
log_level: INFO  # Default log level for router
max_step: 20     # Maximum TTL step; message with step >= max_step is rejected immediately
```

### router/default-router/entrypoint.py
```
﻿import sys

from shell.app.app import App


def main() -> int:
    app = App.init_app(mode='router', runner_root_dir=__file__)
    return app.run_app()

if __name__ == "__main__":
    sys.exit(main())
```

### router/default-router/manifest.yaml
```
﻿name: default-router
mode: router
role: router
type: default
version: 0.1.0
description: "Router for routing agent structure"

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
  router:        #Folder containing <router-name>.route.yaml file

cli_args:
  --node-dir:  #Path to the  node directory
  --task-dir:  #Path to directory containing task files (.md and .yaml); required
  --dry-run:   #Optional; validate router node-dir structure and paths without executing; default empty
  --version:   #Optional; print router version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
  --max-step:  #Optional; maximum TTL step for message routing; default 20
```

### tasker/default-tasker/config/config.yaml
```
name: default-tasker
mode: tasker
role: tasker
type: base
# Default configuration for tasker.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.
log_level: INFO  # Default log level for tasker
source_dir: c:/temp/workspace  # Default source directory
max_step: 20     # Maximum TTL step; message with step >= max_step is rejected immediately
```

### tasker/default-tasker/entrypoint.py
```
﻿"""entrypoint.py
Entry point for tasker-worker.
Contains ONLY method calls — no inline logic.

Exit codes for the external orchestrator:
    0 — success
    1 — error
    2 — timeout
    4 — locked
    5 — question
"""

import sys

from shell.app.app import App


def main() -> int:
    app = App.init_app(mode='tasker', runner_root_dir=__file__)
    return app.run_app()

if __name__ == "__main__":
    sys.exit(main())
```

### tasker/default-tasker/examples/my-task.md
```
# my-task

W katalogu c:/temp
1. Utworz prosty projekt aplikacje ktora dodaje 2 liczby i zwraca wynik
2. W jezyku python
3. Napisz do niego testy jednostkowe
4. Uruchom testy i pokaż wynik
```

### tasker/default-tasker/examples/my-task.yaml
```
﻿name: my-task

# session_id — generated by tasker on each init_task run; used by router to tag outgoing messages.
# Allows distinguishing messages from different runs when stage/done/ is checked for idempotency.
# Do not set manually — tasker overwrites this field on every run.
session_id: null

# node mode type values:
#   agent    — AI agent with LLM (e.g. cli-agent)
#   worker   — background worker with some extra logs
#   router   — router for routing between agents and workers
#   tasker    — task manager for managing tasks and graphs
#   tool     — simple tool without complex logic, e.g. for calling external API or running shell commands

# node role values (examples),usually roles are for agent mode
#   analyzer   — analyzes input and produces report
#   developer  — writes or modifies code
#   architect  — designs solution / produces blueprint
#   deployer   — deploys artifacts to environment
#   reviewer   — reviews and validates output
#   tester     — runs tests and reports results

# node status values:
#   new      — defined in yaml, not yet initialized
#   initialized — initialized, but not yet ready for execution
#   ready    — ready for execution
#   pending  — execution started but not finished
#   success  — completed successfully
#   error    — completed with error
#   question — agent stopped and is waiting for extra input
#   waiting  — waiting for external dependency

graph:

  - node_dir: C:\temp\workspace\step-2
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\agent\cli-agent
    mode: agent
    role: developer
    model: gpt-5-mini
    type: agent
    status: null

  - node_dir: C:\temp\workspace\step-5
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\agent\cli-agent
    mode: agent
    role: reviewer
    model: gpt-5-mini
    type: agent
    status: null

  - node_dir: C:\temp\workspace\step-6
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\agent\cli-agent
    mode: agent
    role: analyzer
    model: gpt-5-mini
    type: agent
    status: null

  - node_dir: C:\temp\workspace\step-7
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\router\default-router
    mode: router
    role: router
    type: router
    status: null

  # Example sub-tasker node (mode: tasker).
  # task_name refers to a subfolder / file pair in source_dir: <task_name>.yaml + <task_name>.md
  # source_dir is optional — inherited from parent CLI --source-dir when omitted.
  - node_dir: C:\temp\workspace\step-8
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\tasker\default-tasker
    mode: tasker
    role: tasker
    type: tasker
    task_name: my-subtask
    source_dir: null
    status: null
```

### tasker/default-tasker/manifest.yaml
```
﻿name: default-tasker
mode: tasker
role: tasker
type: default
version: 0.1.0
description: "Task-level multi-node orchestrator."

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
  task:          #Folder contain task definition files: <task_name>.yaml and <task_name>.md
  ".<node_name>": #Sub node, every node can contain none of some sub nodes

cli_args:
  --node-dir:  #Path to the  node directory
  --dry-run:   #Optional; validate tasker node-dir structure and paths without executing; default empty
  --version:   #Optional; print tasker version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --source-dir: #Required; path to source directory containing task files
  --task-name: #Name of the task to execute; that was name of folder in task repository; 
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
  --max-step:  #Optional; maximum TTL step for message routing; default 20
```

### tools/default-tool/config/config.yaml
```
name: default-tool
mode: tool
role: tool
type: base
# Default configuration for tool.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.
log_level: INFO  # Default log level for tool
```

### tools/default-tool/entrypoint.py
```
﻿import sys

from shell.app.app import App


def main() -> int:
    app = App.init_app(mode='tool', runner_root_dir=__file__)
    return app.run_app()
if __name__ == "__main__":
    sys.exit(main())
```

### tools/default-tool/manifest.yaml
```
﻿name: default-tool
mode: tool
role: tool
type: default
version: 0.1.0
description: "Default tool for do something in agent structure."

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
cli_args:
  --node-dir:  #Path to the  node directory
  --dry-run:   #Optional; validate tool node-dir structure and paths without executing; default empty
  --version:   #Optional; print tool version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
```

### wnioski.md
```
# Wnioski z analizy projektu SHELL — pełny plan działań

> **Cel dokumentu:** kompletny zapis ustaleń analizy, błędów, propozycji i planu rozwoju, tak aby kolejna sesja/agent mógł działać na podstawie tego pliku bez ponownej analizy.
> **Zakres analizy:** `platform/shell/**` + entrypointy w `agent/`, `router/`, `tasker/`, `tools/`, `worker/`. Pominięty katalog `platform/tests/`.
> **Data analizy:** 2026-05-30.

---

## 1. Architektura projektu

SHELL to hierarchiczny, wieloagentowy system orkiestracji w Pythonie, uruchamiany jednowątkowo, z komunikacją między modułami przez system plików.

### 1.1. Komponenty kluczowe
- **App** (`platform/shell/app/app/app.py`) — DOM root; holder wszystkich referencji do modułów (`AppNode`, `AppRunner`, `AppConfig`, `AppTrace`, `Result`, `Runtime`, `AppProperties`).
- **AppRunner** (`platform/shell/app/app_runner/app_runner.py`) — dispatcher mode'ów: `agent`, `router`, `tasker`, `tool`, `worker`.
- **AppNode** (`platform/shell/app/app_node/`) — nadrzędny `Node` aplikacji; trzyma `node_dir` z CLI (`--node-dir`) lub fallback `runner_root_dir / ".node"`.
- **Graph** (`platform/shell/structure/graph/graph/graph.py`) — lista `SubNode` ładowana z YAML.
- **Node** (`platform/shell/structure/node/node/node.py`) — struktura katalogów na dysku: `.node/input/`, `output/`, `stage/`, `logs/`, `config/`, ewentualnie `archive/`, `temp/`.
- **Stage** (`platform/shell/structure/stage/`) — event-store statusów wiadomości: `active`, `pending`, `history`, `ignored`, `dead`, `done`.
- **Tasker** (`platform/shell/module/tasker/`) — executor głównego taska; inicjalizuje graph, uruchamia iteracje.
- **Router** (`platform/shell/module/router/`) — routuje wiadomości między node'ami na podstawie graph order i role mappingu.
- **Agent** (`platform/shell/module/agent/`) — wykonuje pracę AI; buduje prompt, wywołuje Copilot CLI, zwraca output.
- **Worker / Tool** — pomocnicze moduły wykonawcze (mode'y `worker`, `tool`).
- **Komponenty wspólne** (`platform/shell/component/`): `cli`, `command`, `config`, `locker`, `manifest`, `message`, `placeholders`, `process`, `prompt`, `prompt_file`, `result`, `runtime`.
- **Logger** (`platform/shell/logger/logger.py`) — globalny logger.
- **Status** (`platform/shell/status/`) — `module_status`, `status` (statusy maszyny stanów).
- **UtilsPath** (`platform/shell/utils/path/`) — JEDYNY gateway do FS; metody: `mkdir`, `exists`, `is_file`, `is_dir`, `is_symlink`, `read_text`, `read_text_safe`, `write_text`, `unlink`, `rmtree`, `copy_to`, `move`, `iterdir`, `glob`, `rglob`.

### 1.2. Przepływ wykonania
1. Entrypoint (np. `tasker/default-tasker/entrypoint.py`) woła `App.init_app(mode='tasker', runner_root_dir=__file__)`.
2. `Tasker.init_graph()` wczytuje YAML, tworzy strukturę katalogów `.node/<sub_node_name>/...` dla każdego node'a w grafie.
3. Pętla iteracyjna: `Router(READY) → Agent(processes) → Router(routes responses) → ... → DONE`.
4. Komunikacja: każdy moduł czyta/pisze pliki w stage'ach swojego node'a; brak shared memory.

### 1.3. Konwencje (z `copilot-instructions.md` + `python.good_practics.md`)
- **Sloty `_<nazwa>`** prywatne, dostęp z zewnątrz **tylko** przez property `<nazwa>_`.
- **Wewnątrz klasy** też używamy property `nazwa_`, **nigdy** `_nazwa` wprost.
- `__init__` **tylko zeruje sloty** do `None`/wartości domyślnych — żadnej logiki, żadnych instancji obiektów podrzędnych.
- Obiekty podrzędne tworzone **lazy w property** — property tworzy instancję, ale **nie inicjalizuje** jej.
- Inicjalizacja w `internal/_init_<nazwa>.py`, woła ją publiczna `init_<nazwa>()`.
- `_init_*` korzysta z property, nie ze slotu.
- Walidacja slotów wymaganych: `internal/_assert_<nazwa>.py`, wywołane w property.
- **Zakaz** `if ... raise` inline w property.
- Wszystkie operacje FS przez `UtilsPath` — **zakaz** `Path.mkdir/read_text/...`, `shutil`, `os`.
- Każda akcja mogąca rzucić błąd otoczona `record_*` (przed/po).
- Brak komentarzy w metodach Pythona, a istniejące się usuwa.
- Importy zawsze na górze pliku.
- Pełne nazwy zmiennych, zero skrótów.
- Nazwy metod publicznych: `<akcja>_<na_czym>` (np. `clean_node_input`, nigdy `clean_input`).
- Nazwa funkcji w `internal/_X.py` musi być `_X`.

---

## 2. Mocne strony

1. **DOM pattern** — czysta hierarchia z back-reference `_app` w każdym module.
2. **Lazy initialization** — większość property tworzy obiekty na żądanie.
3. **Separation of concerns** — `internal/` z dedykowanymi `_init_*`, `_assert_*`, `_validate_*`.
4. **File-based communication** — agenci przez katalogi `.node/`, brak tight coupling.
5. **Comprehensive status tracking** — Stage z 6 statusami (active/pending/history/ignored/dead/done).
6. **Type hints i `Optional`** — szeroko stosowane.
7. **UtilsPath abstraction** — jeden gateway do FS (z wyjątkami do naprawienia).
8. **Spójne entrypointy** — wszystkie używają `App.init_app(mode=..., runner_root_dir=__file__)`.
9. **Konwencja `<typ>:snake_case`** dla ID node'ów (zgodne z KG-MASTER).

---

## 3. Słabe strony / dług techniczny (przegląd)

- Init logic w `__init__` zamiast lazy property (Result w App).
- Direct `_slot` access spoza klasy-właściciela (3+ miejsca).
- Status (klasa) zamiast instancji w slocie Graph.
- Brakujący import `Path` w Node, mimo użycia w property.
- Validation w property zamiast w `_assert_*` (AppRunner.mode_).
- Init logic split między `__init__` a property/init_ (Cli).
- Property robi więcej niż lazy creation (Graph._graph_path_, AppRunner.mode_).
- Brak `record_*` wokół potencjalnie błędnych akcji (Locker).
- Niepoprawny `mode` w entrypoincie default-tool.
- Runtime tworzony bez `_app`, potem `_app` ustawiany manualnie.
- Możliwe nieużywane importy (`shutil` w `_init_agent_command.py` — do potwierdzenia).
- Komentarz `_graph_path_`: „to raczej do wywalenia" — oznacza świadomy dług.

---

## 4. Lista znalezionych błędów (TOP 15) — z lokalizacją

| # | Plik | Linia (przybl.) | Typ | Opis |
|---|------|-----------------|-----|------|
| 1 | `platform/shell/app/app/app.py` | 54 | Init logic w `__init__` | `self._result = Result(self)` — powinno być `None`, `Result` tworzony lazy w property `result_` (która już istnieje). |
| 2 | `platform/shell/structure/graph/graph/graph.py` | 27 | Type error | `self._status = Status` — zapisuje klasę zamiast instancji. Powinno `None` lub `Status.NULL`. |
| 3 | `platform/shell/structure/node/node/node.py` | top | Missing import | `Path` używany w property `node_dir_`, brak `from shell.utils.path.path import Path`. |
| 4 | `tools/default-tool/entrypoint.py` | 10 | Logic error | `mode='tasker'` zamiast `mode='tool'`. |
| 5 | `platform/shell/app/app/app.py` | 61 | Direct slot access | `self._result._status = status` — pisze w prywatny slot innej klasy. Powinno: `self.result_.set_status(status)` (dodać setter). |
| 6 | `platform/shell/app/app/app.py` | 134 | Direct slot access | `self._runtime._app = self` — bezpośredni zapis cudzego slotu. Powinno: wstrzyknięcie `app` w `init_runtime` lub setter. |
| 7 | `platform/shell/component/cli/cli/cli.py` | 42 | Direct slot access | `self._cli_properties._cli = self` — jak wyżej. |
| 8 | `platform/shell/app/app_runner/app_runner.py` | 87 | Validation w property | `mode_` property robi `raise ValueError(...)`. Powinno: walidacja w `internal/_assert_mode_valid.py`, property tylko zwraca. |
| 9 | `platform/shell/component/cli/cli/cli.py` | 47-48 | Init logic w metodzie | `init_cli()` zawiera `append_config_value(...)` zamiast delegować całość do `internal/_init_cli.py`. |
| 10 | `platform/shell/component/locker/locker.py` | 41-51 | Init logic w metodzie | `lock_()` zawiera acquire logic — powinno być w `internal/_init_locker.py` lub `internal/_acquire_locker.py`. |
| 11 | `platform/shell/structure/graph/graph/graph.py` | 45 | Property robi computacje | `_graph_path_` property robi resolve+concat. Konwertuj na slot wypełniany w `_init_graph`. Komentarz autora: „do wywalenia". |
| 12 | `platform/shell/component/cli/cli/cli.py` | 31-34 | Config append w `__init__` | Wartości configu pchane w property `cli_config_` lub `__init__` zamiast w external initializer. |
| 13 | `platform/shell/module/agent/agent_command/internal/_init_agent_command.py` | ~7 | Possibly unused import | `import shutil` — sprawdzić użycie. |
| 14 | `platform/shell/structure/sub_node/sub_node_properties/sub_node_properties.py` | ~194 | Concern | `init_sub_node_properties()` — zweryfikować, czy faktycznie tylko inicjalizuje sloty. |
| 15 | `platform/shell/component/locker/` | — | Brak `record_*` | `Locker.lock_()` może rzucić `LockError` — brak `record_error/info` przed/po. Konwencja wymaga. |

---

## 5. Plan poprawek — 3 priorytety

### 5.1. Priorytet 1 — Blockers (logiczne błędy)

#### P1.1 — `App.__init__` Result lazy
- **Plik:** `platform/shell/app/app/app.py:54`
- **Zmiana:**
  - Z: `self._result: Result | None = Result(self)`
  - Na: `self._result: Result | None = None`
- **Uzasadnienie:** `result_` property już realizuje lazy creation; podwójna inicjalizacja jest niepotrzebna i łamie wzorzec.

#### P1.2 — `Graph.__init__` Status type
- **Plik:** `platform/shell/structure/graph/graph/graph.py:27`
- **Zmiana:**
  - Z: `self._status = Status`
  - Na: `self._status = None` (lub `Status.NULL` jeśli istnieje wartość domyślna)
- **Uzasadnienie:** zapisanie klasy zamiast instancji to bug — każde użycie `status_` zwraca klasę i łamie kontrakt.

#### P1.3 — `Node` brakujący import `Path`
- **Plik:** `platform/shell/structure/node/node/node.py` (nagłówek)
- **Zmiana:** dodać `from shell.utils.path.path import Path`
- **Uzasadnienie:** property `node_dir_` używa `Path` — dziś zadziała tylko jeśli inny moduł wcześniej je zaimportował przez `__init__.py`.

#### P1.4 — `default-tool` mode
- **Plik:** `tools/default-tool/entrypoint.py:10`
- **Zmiana:** `mode='tasker'` → `mode='tool'`
- **Uzasadnienie:** entrypoint deklaruje niewłaściwy tryb; `AppRunner` rozpozna go jako tasker.

#### Verification P1
- Każdy entrypoint (`agent/cli-agent`, `router/default-router`, `tasker/default-tasker`, `tools/default-tool`, `worker/default-worker`) odpalony i `App.init_app(...)` przechodzi bez `AttributeError`/`TypeError`.
- `grep -rn "self._result = Result"` w `platform/shell/app/` — zero wyników.
- `grep -rn "self._status = Status$"` w `platform/shell/structure/graph/` — zero wyników.

### 5.2. Priorytet 2 — Naruszenia konwencji

#### P2.1 — Result setter zamiast direct slot
- **Plik:** `platform/shell/app/app/app.py:61` + `platform/shell/component/result/...`
- **Zmiana:** dodać metodę `set_status(status)` w klasie `Result`; w `App` wołać `self.result_.set_status(status)`.

#### P2.2 — Runtime injection
- **Plik:** `platform/shell/app/app/app.py:134` + `platform/shell/component/runtime/...`
- **Zmiana:** `init_runtime()` przyjmuje `app` lub Runtime ma setter `set_app(app)`. Eliminacja `self._runtime._app = self`.

#### P2.3 — CliProperties injection
- **Plik:** `platform/shell/component/cli/cli/cli.py:42`
- **Zmiana:** analogicznie jak P2.2 — setter lub wstrzyknięcie w init.

#### P2.4 — `_assert_mode_valid`
- **Pliki:**
  - `platform/shell/app/app_runner/internal/_assert_mode_valid.py` (NOWY)
  - `platform/shell/app/app_runner/app_runner.py:87`
- **Zmiana:** wynieść walidację z property `mode_` do `_assert_mode_valid(mode)`. Property zwraca tylko `self._mode`. Wywołanie asserta w setterze/initializer.

#### P2.5 — `_init_cli` przejmuje całość
- **Pliki:**
  - `platform/shell/component/cli/cli/internal/_init_cli.py` (rozszerzyć)
  - `platform/shell/component/cli/cli/cli.py:31-34, 47-48`
- **Zmiana:** wszystkie `append_config_value` i logika konfiguracyjna do `_init_cli`. `init_cli()` woła tylko `_init_cli(self, ...)`.

#### P2.6 — Locker acquire wydzielenie
- **Pliki:**
  - `platform/shell/component/locker/internal/_acquire_locker.py` (NOWY)
  - `platform/shell/component/locker/locker.py:41-51`
- **Zmiana:** logika acquire'a w internal funkcji; `lock_()` woła `_acquire_locker(self)`. Otoczyć `record_error/info`.

#### Verification P2
- `grep -rn "self\._\(result\|runtime\|cli_properties\)\." platform/shell/` — wynik tylko w klasie-właścicielu.
- `grep -rn "raise " platform/shell/**/<plik>_<nazwa>.py` poza `internal/` — zero w property.

### 5.3. Priorytet 3 — Cleanup

#### P3.1 — `Graph._graph_path_` jako slot
- **Plik:** `platform/shell/structure/graph/graph/graph.py`
- **Zmiana:** zastąpić computującą property zwykłym slotem `_graph_path` wypełnianym w `internal/_init_graph.py` (resolve+concat tam się dzieje raz).

#### P3.2 — Audit `record_*`
- **Zakres:** wszystkie publiczne metody w `module/`, `component/locker/`, `component/process/`, `component/command/`, każde I/O na pliku.
- **Zmiana:** owinięcie `record_info` przed, `record_error` w `except`, `record_info` po sukcesie.

#### P3.3 — Unused imports cleanup
- **Plik:** `platform/shell/module/agent/agent_command/internal/_init_agent_command.py` + całe `internal/`
- **Zmiana:** uruchomić `ruff --select F401` lub manualny audit; usunąć unused (m.in. potencjalnie `shutil`).

#### P3.4 — Nazewnictwo metod
- **Zakres:** audit czy wszystkie publiczne metody mają formę `<akcja>_<na_czym>` (np. brak `clean_input`, ma być `clean_node_input`). Skontrolować szczególnie `Node`, `SubNode`, `Stage`.

#### P3.5 — `__init__` purity
- **Zakres:** każdy `__init__` w `platform/shell/` powinien tylko zerować sloty. Zrobić listę naruszeń przez grep `def __init__` + manualną inspekcję ciał konstruktorów.

#### Verification P3
- Smoke test pełnego cyklu: `tasker → router → agent → router → DONE`.
- `ruff check platform/shell/` (po włączeniu reguły F401, F811, F841) — czysto.

---

## 6. Konkretne zmiany — gotowe snippety

### Snippet 1 — App lazy result
```python
# platform/shell/app/app/app.py (fragment __init__)
self._result: Result | None = None  # zamiast Result(self)
```

### Snippet 2 — Graph status
```python
# platform/shell/structure/graph/graph/graph.py (fragment __init__)
self._status = None  # zamiast self._status = Status
```

### Snippet 3 — Node import
```python
# platform/shell/structure/node/node/node.py (top of file)
from shell.utils.path.path import Path
```

### Snippet 4 — default-tool
```python
# tools/default-tool/entrypoint.py
app = App.init_app(mode='tool', runner_root_dir=__file__)  # zamiast 'tasker'
```

### Snippet 5 — Result setter
```python
# platform/shell/component/result/result/result.py
def set_status(self, status: Status) -> None:
    self._status = status

# platform/shell/app/app/app.py
if status is not None:
    self.result_.set_status(status)  # zamiast self._result._status = status
```

### Snippet 6 — _assert_mode_valid
```python
# platform/shell/app/app_runner/internal/_assert_mode_valid.py
_MODES = {'agent', 'router', 'tasker', 'tool', 'worker'}

def _assert_mode_valid(mode: str | None) -> None:
    if mode is not None and mode not in _MODES:
        raise ValueError(f"mode must be one of {sorted(_MODES)!r}, got {mode!r}")
```

### Snippet 7 — _init_cli
```python
# platform/shell/component/cli/cli/internal/_init_cli.py
def _init_cli(cli: 'Cli', argv: list[str] | None = None) -> None:
    cli.cli_config_.append_config_value('runner_root_dir', cli.runner_root_dir_, 'cli')
    # ... reszta logiki przeniesiona z cli.py
```

### Snippet 8 — _acquire_locker
```python
# platform/shell/component/locker/internal/_acquire_locker.py
def _acquire_locker(locker: 'Locker') -> None:
    locker.app_.trace_.record_info('locker.acquire.begin')
    try:
        # ... acquire logic
        locker.app_.trace_.record_info('locker.acquire.ok')
    except Exception:
        locker.app_.trace_.record_error('locker.acquire.fail')
        raise
```

---

## 7. Mapa kolejności prac (sprint plan)

### Sprint 1 — Blockers (1 sesja)
1. P1.1 → P1.2 → P1.3 → P1.4 (4 zmiany w 4 plikach)
2. Smoke test wszystkich 5 entrypointów.
3. Commit: `fix: P1 blockers — lazy Result, Status instance, Path import, default-tool mode`.

### Sprint 2 — Konwencje (1-2 sesje)
4. P2.4 (`_assert_mode_valid`) — najprostsza, samodzielna.
5. P2.1, P2.2, P2.3 — direct slot access przez settery (każda klasa w osobnym commitcie).
6. P2.5 — przeniesienie logiki Cli do `_init_cli`.
7. P2.6 — wydzielenie acquire z Lockera + `record_*`.
8. Commit per zmiana, nazewnictwo: `refactor: <obszar> — <co>`.

### Sprint 3 — Cleanup (1 sesja)
9. P3.1 — `Graph._graph_path_` na slot.
10. P3.2 — audit `record_*` (najwięcej pracy, zaplanować osobno).
11. P3.3 — unused imports.
12. P3.4 — audit nazewnictwa.
13. P3.5 — audit `__init__`.

---

## 8. Dalsze kroki rozwoju (poza naprawami)

### 8.1. Krótkoterminowe
- **Logging w `init_*`** — każde `init_X` woła `record_info` z nazwą zasobu i kontekstem.
- **`init_*` audit** — sprawdzić czy każde nazywa się `init_<nazwa>`, a nie `build_*`/`setup_*`/`create_*`.

### 8.2. Średnioterminowe
- **Formalna spec YAML graph** — udokumentować schema (klucze, typy, role, kolejność).
- **JSON Schema dla `task.yaml` i node configs** — walidacja przed parsowaniem.
- **Message envelope versioning** — każdy plik wiadomości w stage'ach ma `schema_version`.
- **Refaktor Runtime** — wstrzyknięcie `app` w init zamiast post-set (zamknięcie P2.2).

### 8.3. Długoterminowe
- **Multi-run parallel support** — obecnie single-run; lokowanie node'ów per run-id.
- **Structured logging (JSON)** — łatwiejsza analiza i indexowanie do KG.
- **DSL dla tasków** — wyższy poziom abstrakcji niż surowy YAML graph.
- **Integracja z KG-MASTER** — automatyczne raportowanie node'ów/decyzji do grafu wiedzy.

### 8.4. Testy (obecnie poza zakresem)
- Snapshot tests struktury katalogów `.node/`/`stage/`.
- Integration tests pełnego cyklu `tasker→router→agent→...→DONE`.
- Coverage `internal/_init_*` (dziś niepokryte).

---

## 9. Ocena ogólna

- **Fundamenty:** solidne (DOM, lazy, file-based, UtilsPath, modularność).
- **Dług techniczny:** ~20-30%, głównie w przestrzeganiu własnych konwencji.
- **Ryzyko produkcyjne:** błędy P1 mogą powodować runtime errors w nietypowych ścieżkach (wrong mode, Status klasa, missing import). P1.4 szczególnie — `default-tool` po prostu robi nie to co powinien.
- **Maintainability:** wysoka po naprawie P1+P2; pattern jest zrozumiały i powtarzalny.
- **Rekomendacja:** zacząć od Sprint 1 (P1) — niskie ryzyko, wysoki zysk. Potem Sprint 2 systematycznie.

---

## 10. Notatki dla kolejnej sesji

- **Konwencja krytyczna:** `__init__` zerujemy, lazy w property, init w `internal/_init_*`. Naruszenia tego są największym długiem.
- **UtilsPath only** — przed dodaniem `import shutil`/`import os` w nowym kodzie: nie. Użyj `shell/utils/path/utils_path.py`.
- **`record_*` always** — przed każdą akcją mogącą rzucić błąd.
- **Workflow `.done`** — git add/commit/push + nowy branch `<N+1>_feature` w `C:\Users\palysiewicz\IdeaProjects\schell\platform`.
- **Pominięte z analizy:** cały `platform/tests/`.
- **Niezweryfikowane (wymaga ponownego sprawdzenia):** numeracja linii w tabeli z sekcji 4 — to przybliżenia, przed implementacją zweryfikować exact lines (`grep -n` lub read_file na konkretnym fragmencie).
```

### worker/default-worker/config/config.yaml
```
# Default configuration for tasker-worker.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.

# Number of retries on failure (0 = no retry)
retries: 0

# If true, do not ask user for input (non-interactive mode)
no_ask_user: true

# If true, run in autopilot mode (no confirmation prompts)
autopilot: true
```

### worker/default-worker/entrypoint.py
```
﻿import sys

from shell.app.app import App

def main() -> int:
    app = App.init_app(mode='worker', runner_root_dir=__file__)
    return app.run_app()

if __name__ == "__main__":
    sys.exit(main())
```

### worker/default-worker/manifest.yaml
```
﻿name: default-worker
mode: worker
role: worker
type: default
version: 0.1.0
description: "Default worker for do something in agent structure."

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
cli_args:
  --node-dir:  #Path to the  node directory
  --dry-run:   #Optional; validate worker node-dir structure and paths without executing; default empty
  --version:   #Optional; print worker version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
```
