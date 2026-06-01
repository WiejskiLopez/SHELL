### platform/shell/structure/graph/graph/graph.py
```
﻿from __future__ import annotations

from shell.structure.graph.graph.internal._init_graph import _init_graph
from shell.structure.sub_node.sub_node.sub_node import SubNode
from shell.status.status import Status
from shell.constants.constants import DOT_NODE, DIR_TASK


class Graph:
    """Graph nodes loaded from a task YAML.

    ``self.graph_nodes`` is an empty list until ``init_graph`` is called,
    at which point it is populated as ``list[SubNode]`` from ``task_graph_yaml``.

    Supports iteration, len, and indexing so it can be used directly
    wherever a sequence of graph nodes is expected.
    """

    __slots__ = ("_sub_nodes", "_app", "_status")

    def __init__(self, app=None) -> None:
        self._sub_nodes: list[SubNode] = []
        self._app = app
        self._status = Status

    @property
    def status_(self):
        return self._status

    # ------------------------------------------------------------------ #
    # Sequence protocol                                                    #
    # ------------------------------------------------------------------ #

    def __iter__(self):
        return iter(self._sub_nodes)

    def __len__(self) -> int:
        return len(self._sub_nodes)

    def __getitem__(self, index):
        return self._sub_nodes[index]

    # ------------------------------------------------------------------ #
    # Pure queries                                                         #
    # ------------------------------------------------------------------ #

    @property
    def _graph_path_(self):  ## to raczej do wywalenia, graph powinien dostawac to jako argument, a nie sam sobie wyliczac
        """Return the resolved path to the graph YAML file."""
        return (self._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve() / f"{self._app.app_node_.node_.node_name_}.yaml"

    @property
    def sub_nodes_(self) -> list:
        return self._sub_nodes

    # ------------------------------------------------------------------ #
    # Mutating operations                                                  #
    # ------------------------------------------------------------------ #

    def init_graph(
        self,
        reader=None,
        writer=None,
    ) -> None:
        _init_graph(self, reader=reader, writer=writer)
```

### platform/shell/structure/graph/graph/internal/__init__.py
```
```

### platform/shell/structure/graph/graph/internal/_init_graph.py
```
﻿"""_init_graph.py
Private. Load graph YAML from disk, validate and initialize graph_nodes.
"""

from __future__ import annotations

import yaml

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.status.status import Status
from shell.structure.sub_node.sub_node.sub_node import SubNode
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_graph(graph, reader=None, writer=None) -> None:
    if reader is None:
        reader = default_read_utf8
    if writer is None:
        writer = default_write_utf8

    task_graph_dict = graph._app.app_node_.node_.node_task_.task_graph_dict_
    task_dir = (graph._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()

    sub_nodes = []
    for sub_node_dict in task_graph_dict['graph']:
        sub_node = SubNode(app=graph._app)
        sub_node.init_sub_node(sub_node_dict, writer=writer, reader=reader)
        sub_nodes.append(sub_node)
    graph._sub_nodes = sub_nodes

    task_name = graph._app.app_node_.node_.node_task_.task_name_
    yaml_path = task_dir / f'{task_name}.yaml'
    Path.write_text(yaml_path, yaml.dump(task_graph_dict, default_flow_style=False, allow_unicode=True))
    graph._app.app_trace_.record_info(
        'graph._init_graph._init_graph',
        f'persisted graph status to {yaml_path.name}'
    )
```

### platform/shell/structure/graph/graph/internal/_load_graph_yaml.py
```
﻿from __future__ import annotations

import yaml

from shell.module.tasker.internal._assert_task_graph_yaml_valid import _assert_task_graph_yaml_valid


def _load_graph_yaml(graph) -> dict:
    task_yaml_file_body = graph._app.app_node_.node_.node_task_.task_yaml_file_body_
    graph_yaml = yaml.safe_load(task_yaml_file_body)
    _assert_task_graph_yaml_valid(graph_yaml)
    return graph_yaml
```

### platform/shell/structure/graph/graph/internal/_persist_node_status.py
```
﻿from __future__ import annotations

import yaml

from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _persist_node_status(sub_node, app) -> None:
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    if not yaml_files:
        return
    yaml_path = yaml_files[0]
    data = yaml.safe_load(Path.read_text(yaml_path)) or {}
    for node_dict in data.get('graph', []):
        if node_dict.get('node_name') == sub_node.node_name_:
            node_dict['status'] = sub_node.status_.name
            break
    Path.write_text(yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info(
        'graph._persist_node_status._persist_node_status',
        f'persisted status={sub_node.status_.name} for node {sub_node.node_name_} to {yaml_path.name}'
    )
```

### platform/shell/structure/graph/graph_status/graph_status.py
```
﻿"""graph_status.py
GraphStatus — derives overall graph status from node statuses.

Slots:
    _graph    — parent Graph instance (back-reference)
    _app  — parent App instance (back-reference)

Validated properties:
    graph_status_  — overall Status derived from node statuses
"""

from __future__ import annotations
class Status(int, Enum):
    SUCCESS = 0
    ERROR = 1
    TIMEOUT = 2
    WARNING = 3
    LOCKED = 4
    QUESTION = 5
    WAITING = 6
    SKIP = 7
    READY = 8
    INITIALIZED = 9
    NULL = 10
    DONE = 11
    CRITICAL = 99tam gdzie uzywana 
from shell.status.status import Status

_STATUS_PRIORITY = (
    Status.ERROR,
    Status.LOCKED,
    Status.TIMEOUT,
    Status.WAITING,
    Status.QUESTION,
)
_SUCCESS_STATES = frozenset({Status.SUCCESS, Status.SKIP})


class GraphStatus:
    """Derives overall graph status from node statuses (priority order).

    Priority: ERROR > LOCKED > TIMEOUT > WAITING > QUESTION > SUCCESS.
    Returns Status.SUCCESS only when all nodes are in {SUCCESS, SKIP}.
    """

    __slots__ = ("_graph", "_app")

    def __init__(self, graph) -> None:
        self._graph = graph
        self._app = graph._app

    @property
    def graph_status_(self) -> Status:
        """Derive overall graph status from node statuses (priority order)."""
        sub_nodes = self._graph.sub_nodes_
        statuses = {n.node_.status_ for n in sub_nodes}
        for s in _STATUS_PRIORITY:
            if s in statuses:
                return s
        if all(n.node_.status_ in _SUCCESS_STATES for n in sub_nodes):
            return Status.SUCCESS
        for node in sub_nodes:
            if node.node_.status_ not in _SUCCESS_STATES:
                return node.node_.status_
        return Status.SUCCESS
```

### platform/shell/structure/node/__init__.py
```
﻿from shell.structure.node.node.node import Node
```

### platform/shell/structure/node/node/__init__.py
```
﻿from shell.structure.node.node.node import Node
```

### platform/shell/structure/node/node/internal/__init__.py
```
```

### platform/shell/structure/node/node/internal/_assert_config_yaml_exists.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_config_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_validate_node] Node config not found: {path}")
```

### platform/shell/structure/node/node/internal/_assert_input_dir_exists.py
```
﻿"""_assert_input_dir_exists.py
Responsible for one thing: raising FileNotFoundError when the node input/ directory is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_input_dir_exists(path: PathType) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[_validate_node] Node input/ not found: {path}")
```

### platform/shell/structure/node/node/internal/_assert_node_dir_is_dir.py
```
﻿"""_assert_node_dir_is_dir.py
Responsible for one thing: raising FileNotFoundError when a node directory does not exist.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_node_dir_is_dir(path: PathType, context: str) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[{context}] Node directory not found: {path}")
```

### platform/shell/structure/node/node/internal/_assert_node_dir_set.py
```
"""_assert_node_dir_set.py
Responsible for one thing: raising ValueError when node_dir is not set.
"""

from __future__ import annotations


def _assert_node_dir_set(node_dir: str | None) -> None:
    if node_dir is None:
        raise ValueError("[Node] node_dir is not set")
```

### platform/shell/structure/node/node/internal/_assert_node_name_resolvable.py
```
"""_assert_node_name_resolvable.py
Responsible for one thing: raising ValueError when neither _node_name nor _node_dir is set.
"""


def _assert_node_name_resolvable(node_name: str | None, node_dir: str | None) -> None:
    """Raise ValueError if both node_name and node_dir are falsy."""
    if not node_name and not node_dir:
        raise ValueError("[Node] _node_name is not set and _node_dir is not set")
```

### platform/shell/structure/node/node/internal/_assert_source_dir_set.py
```
﻿from shell.utils.path.path import PathType
from __future__ import annotations



def _assert_source_dir_set(source_dir: PathType | None) -> None:
    if source_dir is None:
        raise RuntimeError("[Node] source_dir is not set — pass --source-dir to the CLI")
```

### platform/shell/structure/node/node/internal/_clean_dir.py
```
﻿"""_clean_dir.py
Remove all files and subdirectories inside a single directory.
"""
from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_dir(
    target: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all contents of *target* directory (if it exists).

    Does NOT remove the directory itself.
    """
    if not Path.exists(target):
        return
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node/internal/_clean_input.py
```
﻿"""_clean_input.py
Responsible for one thing: removing all contents of the input/ directory inside a node.
"""

from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_input(
    node: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all files and subdirectories inside <node>/input/."""
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    target = node / ".node" / "input"
    if not Path.exists(target):
        return
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node/internal/_clean_node.py
```
from __future__ import annotations


def _clean_node(node) -> None:
    node.node_input_.clean_node_input()
    node.node_output_.clean_node_output()
    node.node_temp_.clean_node_temp()
    node.node_scripts_.clean_node_scripts()
    node.node_logs_.clean_node_logs()
    node.node_stage_.clean_node_stage()
    node.node_archive_.clean_node_archive()
```

### platform/shell/structure/node/node/internal/_clean_output.py
```
﻿"""_clean_output.py
Responsible for one thing: removing all contents of the output/ directory inside a node.
"""

from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_output(
    node: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all files and subdirectories inside <node>/output/."""
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    target = node / ".node" / "output"
    if not Path.exists(target):
        return
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node/internal/_create_node.py
```
﻿from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace

_DOT_NODE_DIRS = ("input", "output", "archive", "temp", "logs", "config", "scripts")


def _create_node(node_dir: PathType, make_dirs: Callable[[PathType], None], trace: 'AppTrace | None' = None) -> None:
    dot_node = node_dir / DOT_NODE
    for sub in _DOT_NODE_DIRS:
        path = dot_node / sub
        make_dirs(path)
        if not Path.exists(path):
            raise RuntimeError(f'[node._create_node] failed to create directory: {path}')
        # if trace is not None:
        #     trace.record_info('node._create_node._create_node', f'mkdir {path}')
```

### platform/shell/structure/node/node/internal/_init_node.py
```
﻿from __future__ import annotations


from shell.structure.node.node.internal._validate_node import _validate_node
from shell.structure.node.node.internal._assert_source_dir_set import _assert_source_dir_set
from shell.utils.path.path import Path, PathType

def _init_node(node, node_dir: str, node_config=None) -> None:
    node._node_dir = node_dir
    node._node_name = Path.new(node_dir).name
    node_dir = node.node_dir_

    node.node_config_.init_node_config()
    node.node_input_.init_node_input()
    node.node_output_.init_node_output()
    node.node_logs_.init_node_logs()
    node.node_archive_.init_node_archive()

    source_dir = node._app.cli_.cli_properties_.source_dir_
    _assert_source_dir_set(source_dir)
    if node._app.cli_.cli_properties_.mode_ == 'agent':
        node.node_prompt_.init_node_prompt()
    if node._app.cli_.cli_properties_.mode_ == 'router':
        node.node_stage_.init_node_stage()
    if node._app.cli_.cli_properties_.mode_ == 'tasker':
        node.node_task_.init_node_task()
    _validate_node(node_dir)
```

### platform/shell/structure/node/node/internal/_validate_node.py
```
﻿from shell.utils.path.path import PathType
from __future__ import annotations


from shell.structure.node.node.internal._assert_node_dir_is_dir import _assert_node_dir_is_dir
from shell.structure.node.node.internal._assert_config_yaml_exists import _assert_config_yaml_exists
from shell.structure.node.node.internal._assert_input_dir_exists import _assert_input_dir_exists
from shell.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML, DIR_INPUT


def _validate_node(node_dir: PathType) -> None:
    _assert_node_dir_is_dir(node_dir, '_validate_node')
    _assert_config_yaml_exists(node_dir / DOT_NODE / CONFIG_DIR / CONFIG_YAML)
    _assert_input_dir_exists(node_dir / DOT_NODE / DIR_INPUT)
```

### platform/shell/structure/node/node/node.py
```
﻿"""node.py
Node — single entry point for all node directory operations.

Slots (own, private):
    _node_dir    — raw path string to the node directory (str | None)
    _node_config — lazy NodeConfig instance (NodeConfig | None)
    node_output  — lazy NodeOutput instance (NodeOutput | None)
    node_input   — lazy NodeInput instance (NodeInput | None)

Validated properties:
    node_dir_    — resolved Path from _node_dir; required, raises if not set
    node_name_   — directory name of node_dir_ as node identifier
    node_config_ — lazy NodeConfig instance

Methods:
    clean_node(rmtree, unlink)     — remove output/ archive/ contents
    init_node()             — validate + create dirs
"""

from __future__ import annotations

from shell.structure.node.node.internal._init_node import _init_node
from shell.structure.node.node.internal._clean_node import _clean_node
from shell.structure.node.node.internal._assert_node_dir_set import _assert_node_dir_set
from shell.structure.node.node_archive.node_archive import NodeArchive
from shell.structure.node.node_config.node_config import NodeConfig
from shell.structure.node.node_input.node_input import NodeInput
from shell.structure.node.node_output.node_output import NodeOutput
from shell.structure.node.node_prompt.node_prompt import NodePrompt
from shell.structure.node.node_logs.node_logs import NodeLogs
from shell.structure.node.node_scripts.node_scripts import NodeScripts
from shell.structure.node.node_task.node_task import NodeTask
from shell.structure.node.node_status.node_status import NodeStatus
from shell.structure.node.node_stage.node_stage import NodeStage
from shell.structure.node.node_temp.node_temp import NodeTemp
from shell.status.status import Status

class Node:
    """Typed interface for all node directory operations.

    Owns _node_dir and _config_node. All node-related logic passes through here.
    _app is kept for operations that need logging and runner_root_dir fallback.
    """

    __slots__ = ("_node_dir", "_node_name", "_node_config", "_app", "_node_status", "_node_output", "_node_input", "_node_archive", "_node_prompt", "_node_task", "_node_stage", "_node_logs", "_node_temp", "_node_scripts")

    def __init__(self, app, node_name: str | None = None,
                 role: str | None = None, type: str | None = None, status: Status | None = None) -> None:
        self._app = app
        self._node_dir: str | None = None
        self._node_name: str | None = node_name
        self._node_config: NodeConfig | None = None
        self._node_output: NodeOutput | None = None
        self._node_input: NodeInput | None = None
        self._node_archive: NodeArchive | None = None
        self._node_status = NodeStatus(status)
        self._node_prompt: NodePrompt | None = None
        self._node_task: NodeTask | None = None
        self._node_stage: NodeStage | None = None
        self._node_logs: NodeLogs | None = None
        self._node_temp: NodeTemp | None = None
        self._node_scripts: NodeScripts | None = None

    # -----------------------------------------------------------------------
    # Validated properties (suffix _ convention)
    # -----------------------------------------------------------------------

    @property
    def node_dir_(self) -> Path:
        """Return resolved Path of node_dir. Raises if not set."""
        _assert_node_dir_set(self._node_dir)
        return Path(self._node_dir).resolve()

    @property
    def node_name_(self) -> str:
        """Return the node name: explicit _node_name if set, else directory name of node_dir_."""
        return self._node_name if self._node_name else self.node_dir_.name

    @property
    def node_status_(self) -> NodeStatus:
        """Return the NodeStatus instance for this node."""
        return self._node_status

    @property
    def status_(self) -> Status | None:
        return self._node_status.status_

    @property
    def is_ready_(self) -> bool:
        """Return True when node should be executed (status 'ready')."""
        return self._node_status.is_ready_

    @property
    def node_config_(self) -> NodeConfig:
        """Lazy NodeConfig instance for this node."""
        if self._node_config is None:
            self._node_config = NodeConfig(self._app)
        return self._node_config

    @property
    def node_output_(self) -> NodeOutput:
        """Lazy NodeOutput instance for this node."""
        if self._node_output is None:
            self._node_output = NodeOutput(self._app)
        return self._node_output

    @property
    def node_input_(self) -> NodeInput:
        """Lazy NodeInput instance for this node."""
        if self._node_input is None:
            self._node_input = NodeInput(self._app)
        return self._node_input

    @property
    def node_prompt_(self) -> NodePrompt:
        if self._node_prompt is None:
            self._node_prompt = NodePrompt(self._app)
        return self._node_prompt

    @property
    def node_task_(self) -> NodeTask:
        if self._node_task is None:
            self._node_task = NodeTask(self._app)
        return self._node_task

    @property
    def node_stage_(self) -> NodeStage:
        if self._node_stage is None:
            self._node_stage = NodeStage(self._app)
        return self._node_stage

    @property
    def node_logs_(self) -> NodeLogs:
        if self._node_logs is None:
            self._node_logs = NodeLogs(self._app)
        return self._node_logs

    @property
    def node_archive_(self) -> NodeArchive:
        """Lazy NodeArchive instance for this node."""
        if self._node_archive is None:
            self._node_archive = NodeArchive(self._app)
        return self._node_archive

    @property
    def node_temp_(self) -> NodeTemp:
        if self._node_temp is None:
            self._node_temp = NodeTemp(self._app)
        return self._node_temp

    @property
    def node_scripts_(self) -> NodeScripts:
        if self._node_scripts is None:
            self._node_scripts = NodeScripts(self._app)
        return self._node_scripts

    # -----------------------------------------------------------------------
    # Clean operations
    # -----------------------------------------------------------------------

    def clean_node(self) -> None:
        _clean_node(self)
        self._app.app_trace_.record_info('node.Node.clean_node', 'OK')

    # -----------------------------------------------------------------------
    # Lifecycle operations
    # -----------------------------------------------------------------------

    def init_node(self, node_dir: str) -> None:
        try:
            _init_node(self, node_dir)
        except Exception as exc:
            self._app.app_trace_.record_error_and_raise('node.Node.init_node', exc)



```

### platform/shell/structure/node/node_archive/__init__.py
```
﻿# shell/node_archive package
from shell.structure.node.node_archive.node_archive import NodeArchive
__all__ = ['NodeArchive']
```

### platform/shell/structure/node/node_archive/internal/__init__.py
```
```

### platform/shell/structure/node/node_archive/internal/_clean_node_archive.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_archive(node_archive) -> None:
    node_archive_dir = node_archive.node_archive_dir_
    if not Path.exists(node_archive_dir):
        return
    for item in Path.iterdir(node_archive_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_archive/internal/_save_archive_zip.py
```
﻿"""_save_archive_zip.py
Private. Responsible for one thing: writing a timestamped ZIP archive
containing app metadata and snapshots of input/, output/, logs/, tmp/.
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace

_SNAPSHOT_DIRS = ("input", "output", "logs", "temp")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _save_archive_zip(
    archive_dir: PathType,
    snapshot: dict,
    clock: Callable[[], datetime] | None = None,
    trace: 'AppTrace | None' = None,
) -> None:
    """Write a .zip archive under archive_dir/ capturing this execution snapshot.

    archive_dir: path to the node's archive/ directory.
    snapshot:    dict from result.runner_result (timestamp, status, role, mode, version, start, stop).
    clock:       optional callable () -> datetime for testability.
    """
    if clock is None:
        clock = _utc_now

    ts_dt = clock()
    meta = dict(snapshot)
    meta['timestamp'] = ts_dt.isoformat()

    role = meta['role']
    status = meta.get('status', 'unknown')
    ts = ts_dt.strftime("%Y%m%d_%H%M%S")
    fname = f"{role}_{ts}_{status}.zip"

    node = archive_dir.parent
    zip_path = archive_dir / fname
    if trace is not None:
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'archive_dir exists={Path.exists(archive_dir)} path={archive_dir}')
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'zip_path={zip_path}')
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'meta={meta}')
    Path.mkdir(archive_dir)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
        if trace is not None:
            trace.record_info('node_archive._save_archive_zip._save_archive_zip', 'meta.json written to zip')
        for sub in _SNAPSHOT_DIRS:
            src = node / sub
            if trace is not None:
                trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'scanning dir={src} exists={Path.exists(src)}')
            if not Path.exists(src):
                continue
            for p in Path.rglob(src, "*"):
                if Path.is_file(p):
                    arcname = f"{sub}/{p.relative_to(src)}"
                    zf.write(p, arcname=arcname)
                    if trace is not None:
                        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'archive add {arcname}')
    if trace is not None:
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'zip written size={zip_path.stat().st_size}B')

```

### platform/shell/structure/node/node_archive/node_archive.py
```
﻿from shell.utils.path.path import PathType
"""node_archive.py  (node_archive)
NodeArchive — single entry point for all node archive operations.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_archive()

Methods:
    save_archive(clock)     — write archive ZIP; never raises
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_archive.internal._save_archive_zip import _save_archive_zip
from shell.structure.node.node_archive.internal._clean_node_archive import _clean_node_archive
from shell.constants.constants import DOT_NODE, DIR_ARCHIVE


class NodeArchive:
    """Typed interface for node archive operations.

    Slots:
        _app            — parent App
        _module_status  — ModuleStatus; NEW until init_node_archive() is called
    """

    __slots__ = ("_app", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def node_archive_dir_(self) -> PathType:
        return (self._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_ARCHIVE).resolve()

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
```

### platform/shell/structure/node/node_config/__init__.py
```
﻿from shell.structure.node.node_config.node_config import NodeConfig

__all__ = ["NodeConfig"]
```

### platform/shell/structure/node/node_config/internal/__init__.py
```
```

### platform/shell/structure/node/node_config/internal/_init_node_config.py
```
﻿"""_init_node_config.py
Private. Responsible for one thing: reading config.yaml into NodeConfig._config.
"""

from __future__ import annotations

from shell.app.app.app import App


def _init_node_config(app: App) -> None:
    app.node_config_.init_node_config()
```

### platform/shell/structure/node/node_config/node_config.py
```
﻿"""node_config.py
NodeConfig — loader and holder for node_dir/.node/config/config.yaml.

Slots:
    _app           — parent App (DOM back-reference)
    _config        — Config instance (Config | None)
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_config()

Responsibilities:
    Reads config.yaml from the node directory into a Config object.
    Can also be initialised from data (role, type) without reading from disk.
"""

from __future__ import annotations

from shell.component.config.config.config import Config
from shell.status.module_status.module_status import ModuleStatus
from shell.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML

class NodeConfig:
    """Holds Config object for the node directory.

    Cached via app.node_config_. _config is populated
    by init_node_config() or append_node_config().
    """

    __slots__ = ("_app", "_config", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._config: Config | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    # -----------------------------------------------------------------------
    # Validated property
    # -----------------------------------------------------------------------

    @property
    def config_(self) -> Config:
        if self._config is None:
            self._config = Config(self._app)
        return self._config

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    @property
    def config_dir_(self) -> PathType:
        return self._app.app_node_.node_.node_dir_ / DOT_NODE / CONFIG_DIR

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init_node_config(self) -> None:
        cfg_path = self.config_dir_ / CONFIG_YAML
        self.config_.init_config(cfg_path, source='node')
        self._module_status = ModuleStatus.INIT
```

### platform/shell/structure/node/node_input/__init__.py
```
﻿# shell/node_input package
from shell.structure.node.node_input.node_input import NodeInput
__all__ = ['NodeInput']
```

### platform/shell/structure/node/node_input/internal/__init__.py
```
# input internal package
```

### platform/shell/structure/node/node_input/internal/_assert_input_dir_exists.py
```
﻿"""_assert_input_dir_exists.py
Validate that the input directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_input_dir_exists(input_dir: PathType) -> None:
    if not Path.is_dir(input_dir):
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")
```

### platform/shell/structure/node/node_input/internal/_init_node_input.py
```
﻿from __future__ import annotations

from shell.component.message.message_list.message_list import MessageList
from shell.component.message.message_reader.message_reader import MessageReader
from shell.structure.node.node_input.internal._assert_input_dir_exists import _assert_input_dir_exists
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT

_MESSAGE_SUFFIXES = {".yaml", ".yml"}


def _init_node_input(node_input) -> None:
    node_input._input_dir = (node_input._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT).resolve()
    _assert_input_dir_exists(node_input._input_dir)

    messages = []
    for path in sorted(p for p in Path.iterdir(node_input.input_dir_) if Path.is_file(p) and p.suffix.lower() in _MESSAGE_SUFFIXES):
        reader = MessageReader()
        reader._path = path
        messages.append(reader.read_message_file())

    message_list = MessageList()
    message_list._messages = messages
    node_input._input_message = message_list
```

### platform/shell/structure/node/node_input/node_input.py
```
﻿"""node_input.py
NodeInput: single entry point for reading node input files.

Fields (own):
    input_dir     — path to the input directory (Path)
    input_message — MessageList of loaded messages
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_input()

Methods:
    init_node_input() — load all *.yaml files from input_dir into input_message
"""

from __future__ import annotations


from shell.component.message.message_list.message_list import MessageList
from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_input.internal._init_node_input import _init_node_input
from shell.utils.path.path import Path, PathType


class NodeInput:
    """Manages reading of input files for a single node run.

    input_dir must be set before calling init_node_input.
    init_node_input loads all *.yaml files from input_dir into input_message.
    """

    __slots__ = ("_app", "_input_dir", "_module_status", "_input_message")

    def __init__(self, app) -> None:
        self._app = app
        self._input_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._input_message: MessageList | None = None

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def input_message_(self) -> MessageList:
        return self._input_message

    @property
    def input_dir_(self) -> PathType:
        return self._input_dir

    @property
    def input_files_map_(self) -> dict[File, str]:
        """Return mapping of loaded File objects to their file names."""
        return self._input_files_map

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_input(self) -> None:
        _init_node_input(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_input(self) -> None:
        target = self._input_dir
        if not Path.exists(target):
            return
        for item in Path.iterdir(target):
            try:
                if Path.is_file(item) or Path.is_symlink(item):
                    Path.unlink(item)
                elif Path.is_dir(item):
                    Path.rmtree(item)
            except OSError:
                pass
```

### platform/shell/structure/node/node_logs/__init__.py
```
﻿# shell/node_logs package
from shell.structure.node.node_logs.node_logs import NodeLogs
__all__ = ['NodeLogs']
```

### platform/shell/structure/node/node_logs/internal/__init__.py
```
﻿# shell/node_logs/internal package
```

### platform/shell/structure/node/node_logs/internal/_clean_node_logs.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_logs(node_logs) -> None:
    logs_dir = node_logs.logs_dir_
    if not Path.exists(logs_dir):
        return
    for item in Path.iterdir(logs_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_logs/internal/_init_node_logs.py
```
﻿from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_LOGS


def _init_node_logs(node_logs) -> None:
    node_logs._logs_dir = (node_logs._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_LOGS).resolve()
```

### platform/shell/structure/node/node_logs/node_logs.py
```
﻿from shell.utils.path.path import PathType
"""node_logs.py
NodeLogs: manages the logs directory for a single node run.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_logs()
"""

from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_logs.internal._clean_node_logs import _clean_node_logs
from shell.structure.node.node_logs.internal._init_node_logs import _init_node_logs


class NodeLogs:
    """Manages the logs directory for a single node run.

    Slots:
        _app            — parent App
        _module_status  — ModuleStatus; NEW until init_node_logs() is called
    """

    __slots__ = ("_app", "_logs_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._logs_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def logs_dir_(self) -> PathType:
        return self._logs_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_logs(self) -> None:
        _init_node_logs(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_logs(self) -> None:
        _clean_node_logs(self)
```

### platform/shell/structure/node/node_output/__init__.py
```
﻿# shell/node_output package
from shell.structure.node.node_output.node_output import NodeOutput
__all__ = ['NodeOutput']
```

### platform/shell/structure/node/node_output/internal/__init__.py
```
# output internal package
```

### platform/shell/structure/node/node_output/internal/_assert_output_dir_exists.py
```
﻿"""_assert_output_dir_exists.py
Validate that the output directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise ValueError(f"Output directory does not exist or is not a directory: {output_dir}")
```

### platform/shell/structure/node/node_output/internal/_assert_output_files_found.py
```
﻿from __future__ import annotations

from shell.utils.path.path import PathType


def _assert_output_files_found(output_files: list, output_dir: PathType) -> None:
    if not output_files:
        raise FileNotFoundError(f"[NodeOutput] no file found in output_dir: {output_dir}")
```

### platform/shell/structure/node/node_output/internal/_assert_pending_message_found.py
```
from __future__ import annotations


def _assert_pending_message_found(pending_message) -> None:
    if pending_message is None:
        raise ValueError("[NodeOutput] no PENDING message found in input_message_list")
```

### platform/shell/structure/node/node_output/internal/_clean_node_output.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _clean_node_output(node_output) -> None:
    output_dir = node_output.output_dir_
    if not Path.exists(output_dir):
        return
    for item in Path.iterdir(output_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_output/internal/_format_node_output.py
```
﻿from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.message_name import MessageName
from shell.component.message.message_reader.message_reader import MessageReader
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_validator.message_validator import MessageValidator
from shell.component.message.message_writer.message_writer import MessageWriter
from shell.component.message.source_type.source_type import SourceType
from shell.structure.node.node_output.internal._assert_output_files_found import _assert_output_files_found
from shell.utils.path.path import Path


def _format_node_output(node_output: object) -> None:
    node = node_output._app.app_node_.node_
    output_dir = node_output.output_dir_
    input_message_list = node.node_input_.input_message_

    pending_message = input_message_list.get_message_by_status(MessageStatus.PENDING)
    input_message_meta = pending_message.message_envelope_.message_meta_
    output_message_meta = MessageMeta.reverse_message_meta(input_message_meta)

    output_files = sorted(p for p in Path.iterdir(output_dir) if Path.is_file(p))
    _assert_output_files_found(output_files, output_dir)

    for file_path in output_files:
        body = Path.read_text(file_path)
        if MessageValidator.is_valid_message(body):
            message = MessageReader.read(file_path)
        else:
            envelope = MessageEnvelope.from_meta_and_payload(output_message_meta, body)
            message = Message.from_envelope(envelope, str(file_path), SourceType.FILE)
            MessageWriter.write(file_path, message)

        meta = message.message_envelope_.message_meta_
        if not MessageName.is_valid_name(file_path.name, meta):
            file_path = MessageName.rename_message(file_path, meta)

        node_output._output_message_.append_message(message)
```

### platform/shell/structure/node/node_output/internal/_init_node_output.py
```
﻿from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_node_output(node_output) -> None:
    node_output._output_dir = (node_output._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT).resolve()
```

### platform/shell/structure/node/node_output/node_output.py
```
﻿from shell.utils.path.path import PathType
"""node_output.py
NodeOutput: single entry point for writing node output files.

Fields (own):
    output_dir       — path to the output directory (path)
    output_files_map — dict[File, str] mapping each File to its file_name
    _module_status   — ModuleStatus enum; NEW on construction, INIT after init_node_output()

Methods:
    init_node_output() — mark module as initialised
    save_output() — save all files from output_files_map to output_dir
"""

from __future__ import annotations


from shell.component.message.message_list.message_list import MessageList
from shell.utils.file.File import File
from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_output.internal._assert_output_dir_exists import _assert_output_dir_exists
from shell.structure.node.node_output.internal._clean_node_output import _clean_node_output
from shell.structure.node.node_output.internal._init_node_output import _init_node_output
from shell.structure.node.node_output.internal._format_node_output import _format_node_output


class NodeOutput:
    """Manages writing of output files for a single node run.

    output_dir must exist before calling save_output.
    save_output writes all File objects from output_files_map to output_dir.
    """

    __slots__ = ("_app", "_output_dir", "_output_files_map", "_module_status", "_output_message")

    def __init__(self, app) -> None:
        self._app = app
        self._output_dir: PathType | None = None
        self._output_files_map: dict[File, str] = {}
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._output_message: MessageList | None = None

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def output_message_(self) -> MessageList:
        return self._output_message

    @property
    def output_dir_(self) -> PathType:
        return self._output_dir

    @property
    def output_files_map_(self) -> dict[File, str]:
        """Return mapping of File objects to their file names."""
        return self._output_files_map

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_output(self) -> None:
        _init_node_output(self)
        self._module_status = ModuleStatus.INIT

    def save_output(self) -> None:
        """Save all files from output_files_map to output_dir.

        output_files_map — dict mapping File -> file_name (str).
        Each File is saved under output_dir / file_name.
        """
        output_dir = self.output_dir_
        for file, file_name in self._output_files_map.items():
            file._file_path = output_dir / file_name
            file.save_file()

    def clean_node_output(self) -> None:
        _clean_node_output(self)

    def format_node_output(self) -> None:
        _format_node_output(self)
```

### platform/shell/structure/node/node_port/__init__.py
```
```

### platform/shell/structure/node/node_port/node_port.py
```
﻿"""node_port.py
NodePort — port (Protocol) abstrakcji storage dla operacji na nodzie.

Definiuje kontrakt wymienny między adapterami:
    - FilesystemNodePort  (domyślny, produkcyjny)
    - DbNodePort          (przyszłość: wszystkie operacje node → baza danych)
    - InMemoryNodePort    (testy: brak I/O)

Konwencja:
    PathType przekazywany do każdej metody jest logicznym identyfikatorem
    (np. node_dir / DIR_INPUT / 'task.md'), a nie bezwzględną ścieżką systemu plików.
    Adapter tłumaczy go na właściwe medium (ścieżka, klucz DB, klucz słownika).
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from typing import Protocol, runtime_checkable
from shell.constants.constants import DIR_INPUT


@runtime_checkable
class NodePort(Protocol):
    """Port definiujący wszystkie operacje I/O na strukturze node.

    Każda implementacja musi zapewnić pełną obsługę tych operacji
    dla swojego medium (filesystem, baza danych, pamięć itp.).
    """

    # -----------------------------------------------------------------------
    # Struktura katalogów / kontenerów
    # -----------------------------------------------------------------------

    def makedirs(self, path: PathType) -> None:
        """Utwórz katalog (wraz z rodzicami) lub odpowiednik w medium.

        Filesystem: path.mkdir(parents=True, exist_ok=True)
        DB:         INSERT INTO nodes(id, type) ON CONFLICT DO NOTHING
        """
        ...

    def exists(self, path: PathType) -> bool:
        """Sprawdź czy ścieżka / rekord istnieje."""
        ...

    def rmtree(self, path: PathType) -> None:
        """Usuń katalog rekurencyjnie lub wszystkie rekordy pod tym węzłem.

        Filesystem: shutil.rmtree(path, ignore_errors=True)
        DB:         DELETE FROM node_files WHERE path LIKE 'prefix%'
        """
        ...

    # -----------------------------------------------------------------------
    # Pliki / rekordy
    # -----------------------------------------------------------------------

    def read_text(self, path: PathType) -> str:
        """Odczytaj zawartość pliku lub rekordu jako tekst."""
        ...

    def write_text(self, path: PathType, content: str) -> None:
        """Zapisz tekst do pliku lub rekordu."""
        ...

    def unlink(self, path: PathType) -> None:
        """Usuń pojedynczy plik / rekord.

        Filesystem: path.unlink(missing_ok=True)
        DB:         DELETE FROM node_files WHERE path = ?
        """
        ...

    def list_files(self, path: PathType, suffix: str) -> list[PathType]:
        """Zwróć listę plików / rekordów w danym katalogu o podanym rozszerzeniu.

        Filesystem: sorted(path.glob(f'*{suffix}'))
        DB:         SELECT path FROM node_files WHERE parent = ? AND suffix = ?
        """
        ...

    def move(self, src: PathType, dst: PathType) -> None:
        """Przenieś plik / rekord z src do dst.

        Filesystem: shutil.move(src, dst)
        DB:         UPDATE node_files SET path = ? WHERE path = ?
        """
        ...
```

### platform/shell/structure/node/node_prompt/__init__.py
```
﻿# shell/node_prompt package
from shell.structure.node.node_prompt.node_prompt import NodePrompt
__all__ = ['NodePrompt']
```

### platform/shell/structure/node/node_prompt/internal/__init__.py
```
﻿# shell/node_prompt/internal package
```

### platform/shell/structure/node/node_prompt/internal/_assert_prompt_dir_exists.py
```
﻿"""_assert_prompt_dir_exists.py
Validate that the prompt directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_prompt_dir_exists(prompt_dir: PathType) -> None:
    if not Path.is_dir(Path.new(prompt_dir)):
        raise ValueError(f"Prompt directory does not exist or is not a directory: {prompt_dir}")
```

### platform/shell/structure/node/node_prompt/internal/_init_node_prompt.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.component.prompt_file.prompt_file import PromptFile
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_node_prompt(node_prompt) -> None:
    app = node_prompt._app
    node_prompt._prompt_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT).resolve()
    task_dir = Path.new(app.cli_.cli_properties_.task_dir_)
    role = app.app_properties_.role_
    if role == 'tasker':
        paths = Path.glob(task_dir, '*.prompt.md')
    elif role == 'agent':
        paths = []
        role_tag = f'.{role}.'
        for path in Path.glob(task_dir, '*.prompt.md'):
            name = path.name
            if '.system.' in name:
                if role_tag not in name:
                    paths.append(path)
            else:
                if role_tag in name:
                    paths.append(path)
    else:
        return
    for path in paths:
        file_prompt = PromptFile()
        file_prompt.init_prompt_file(path.name, Path.read_text(path), node_prompt._prompt_dir)
        node_prompt.prompt_.file_prompts_.append(file_prompt)
```

### platform/shell/structure/node/node_prompt/node_prompt.py
```
﻿from shell.utils.path.path import PathType
"""node_prompt.py
NodePrompt: loads all *.prompt.md files from task_dir into a list.

Slots:
    _app           — parent App
    _prompt_dir    — resolved path to the prompt directory
    _prompt        — Prompt instance; file_prompts_ holds loaded *.prompt.md files
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_prompt()

Methods:
    init_node_prompt() — load all *.prompt.md files from task_dir into file_prompt_list
"""

from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_prompt.internal._init_node_prompt import _init_node_prompt
from shell.component.prompt.prompt.prompt import Prompt


class NodePrompt:

    __slots__ = ("_app", "_prompt_dir", "_prompt", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._prompt_dir: PathType | None = None
        self._prompt: Prompt | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def prompt_dir_(self) -> PathType:
        return self._prompt_dir

    @property
    def prompt_(self) -> Prompt:
        if self._prompt is None:
            self._prompt = Prompt(self._app)
        return self._prompt

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_prompt(self) -> None:
        _init_node_prompt(self)
        self._module_status = ModuleStatus.INIT
```

### platform/shell/structure/node/node_scripts/__init__.py
```
```

### platform/shell/structure/node/node_scripts/internal/__init__.py
```
```

### platform/shell/structure/node/node_scripts/internal/_clean_node_scripts.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_scripts(node_scripts) -> None:
    scripts_dir = node_scripts.scripts_dir_
    if not Path.exists(scripts_dir):
        return
    for item in Path.iterdir(scripts_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_scripts/internal/_init_scripts_dir.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_SCRIPTS


def _init_scripts_dir(node_scripts) -> None:
    node_scripts._scripts_dir = (node_scripts._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_SCRIPTS).resolve()
    Path.mkdir(node_scripts.scripts_dir_)
```

### platform/shell/structure/node/node_scripts/node_scripts.py
```
﻿from shell.utils.path.path import PathType
"""node_scripts.py
NodeScripts — scripts directory for a single node.

Slots:
    _scripts_dir   — path to the scripts directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_scripts()
"""

from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_scripts.internal._init_scripts_dir import _init_scripts_dir
from shell.structure.node.node_scripts.internal._clean_node_scripts import _clean_node_scripts


class NodeScripts:
    """Manages the scripts directory for a single node run."""

    __slots__ = ("_app", "_scripts_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._scripts_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def scripts_dir_(self) -> PathType:
        return self._scripts_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_scripts(self) -> None:
        _init_scripts_dir(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_scripts(self) -> None:
        _clean_node_scripts(self)
```

### platform/shell/structure/node/node_stage/__init__.py
```
```

### platform/shell/structure/node/node_stage/internal/__init__.py
```
```

### platform/shell/structure/node/node_stage/internal/_clean_node_stage.py
```
from __future__ import annotations


def _clean_node_stage(node_stage) -> None:
    node_stage.stage_active_.clean_stage_active()
    node_stage.stage_pending_.clean_stage_pending()
    node_stage.stage_history_.clean_stage_history()
    node_stage.stage_ignored_.clean_stage_ignored()
    node_stage.stage_dead_.clean_stage_dead()
    node_stage.stage_done_.clean_stage_done()
```

### platform/shell/structure/node/node_stage/internal/_get_active_files.py
```
﻿from __future__ import annotations


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_ACTIVE


def _get_active_files(node_stage) -> list[PathType]:
    active_dir = node_stage._stage_dir / DIR_STAGE_ACTIVE
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

### platform/shell/structure/node/node_stage/internal/_get_last_message.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_DONE


def _get_last_message(node_stage) -> PathType | None:
    done_dir = node_stage._stage_dir / DIR_STAGE_DONE
    if not Path.exists(done_dir):
        return None
    candidates = [f for f in Path.iterdir(done_dir) if Path.is_file(f)]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_mtime)
```

### platform/shell/structure/node/node_stage/internal/_get_pending_files.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_PENDING


def _get_pending_files(node_stage) -> list[PathType]:
    pending_dir = node_stage._stage_dir / DIR_STAGE_PENDING
    if not Path.exists(pending_dir):
        return []
    return [f for f in Path.iterdir(pending_dir) if Path.is_file(f)]
```

### platform/shell/structure/node/node_stage/internal/_init_node_stage.py
```
﻿from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_STAGE


def _init_node_stage(node_stage) -> None:
    node_stage._stage_dir = (node_stage._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE).resolve()
    node_stage.stage_.init_stage()
```

### platform/shell/structure/node/node_stage/internal/_init_stage_dirs.py
```
﻿from __future__ import annotations


from shell.constants.constants import DIR_STAGE_ACTIVE, DIR_STAGE_PENDING, DIR_STAGE_HISTORY, DIR_STAGE_IGNORED, DIR_STAGE_DEAD, DIR_STAGE_DONE
from shell.utils.path.path import Path, PathType


def _init_stage_dirs(node_stage) -> None:
    stage_dir = node_stage._stage_dir
    for sub in (DIR_STAGE_ACTIVE, DIR_STAGE_PENDING, DIR_STAGE_HISTORY, DIR_STAGE_IGNORED, DIR_STAGE_DEAD, DIR_STAGE_DONE):
        Path.mkdir(stage_dir / sub)
```

### platform/shell/structure/node/node_stage/internal/_move_pending_to_history.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _move_pending_to_history(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_history_.history_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_dead.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_dead(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_dead_.dead_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_history.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_history(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_history_.history_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_ignored.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_ignored(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_ignored_.ignored_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_pending.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_pending(node_stage, filename: str) -> None:
    source = node_stage.stage_active_.active_dir_ / filename
    dest = node_stage.stage_pending_.pending_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_active.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_ACTIVE


def _save_to_active(node_stage, file: PathType, dest_name: str | None = None) -> None:
    name = dest_name if dest_name is not None else file.name
    dest = node_stage._stage_dir / DIR_STAGE_ACTIVE / name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_done.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_DONE


def _save_to_done(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_DONE / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_history.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_HISTORY


def _save_to_history(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_HISTORY / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_pending.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_PENDING


def _save_to_pending(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_PENDING / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/node_stage.py
```
﻿from shell.utils.path.path import PathType
"""node_stage.py
NodeStage — physical stage directory I/O for a single node.

Slots:
    _stage_dir     — resolved path to the stage directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_stage()
"""

from __future__ import annotations


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

```

### platform/shell/structure/node/node_status/__init__.py
```
﻿from shell.structure.node.node_status.node_status import NodeStatus
```

### platform/shell/structure/node/node_status/node_status.py
```
﻿"""node_status.py
NodeStatus — owns and manages the status of a single node.

Slots:
    _status — current Status value (Status | None)

Validated properties:
    status_ — returns current status value

Methods:
    set_status(value) — set status from Status or int
"""

from __future__ import annotations

from shell.status.status import Status


class NodeStatus:
    """Owns and manages the status of a single node."""

    __slots__ = ("_app", "_status")

    def __init__(self, status: Status | int | None = None) -> None:
        self._app = None
        self._status: Status | None = None
        if status is not None:
            self.set_status(status)

    @property
    def status_(self) -> Status | None:
        """Return current status value."""
        return self._status

    @property
    def is_ready_(self) -> bool:
        """Return True when status is READY."""
        return self._status == Status.READY

    def set_status(self, value: Status | int) -> None:
        """Set status from Status enum or int exit code."""
        if isinstance(value, Status):
            self._status = value
        else:
            self._status = Status(value)

    def init_status(self, status_str: str | None) -> None:
        if status_str is None:
            self._status = Status.NULL
        else:
            self._status = Status.from_str(status_str)
```

### platform/shell/structure/node/node_task/__init__.py
```
```

### platform/shell/structure/node/node_task/internal/__init__.py
```
```

### platform/shell/structure/node/node_task/internal/_assert_source_dir_set.py
```
﻿from shell.utils.path.path import PathType
from __future__ import annotations



def _assert_source_dir_set(source_dir: PathType | None) -> None:
    if source_dir is None:
        raise RuntimeError("[NodeTask] source_dir is not set — pass --source-dir to the CLI")
```

### platform/shell/structure/node/node_task/internal/_assert_task_dir_set.py
```
﻿from shell.utils.path.path import PathType


def _assert_task_dir_set(task_dir: PathType | None) -> None:
    if task_dir is None:
        raise RuntimeError("[NodeTask] task_dir is not set — pass --task-dir to the CLI")
```

### platform/shell/structure/node/node_task/internal/_assert_task_md_exists.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_md_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[NodeTask] task MD not found: {path}")
```

### platform/shell/structure/node/node_task/internal/_assert_task_name_set.py
```
from __future__ import annotations


def _assert_task_name_set(task_name: str | None) -> None:
    if not task_name:
        raise ValueError("[NodeTask] --task-name is required")
```

### platform/shell/structure/node/node_task/internal/_assert_task_yaml_exists.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[NodeTask] task YAML not found: {path}")
```

### platform/shell/structure/node/node_task/internal/_assert_task_yaml_in_task_dir.py
```
﻿from shell.utils.path.path import PathType
from __future__ import annotations



def _assert_task_yaml_in_task_dir(yaml_files: list, task_dir: PathType) -> None:
    if not yaml_files:
        raise FileNotFoundError(f"[NodeTask] no .yaml file found in task_dir: {task_dir}")
```

### platform/shell/structure/node/node_task/internal/_init_node_task.py
```
﻿from __future__ import annotations


from shell.structure.node.node_task.internal._assert_source_dir_set import _assert_source_dir_set
from shell.structure.node.node_task.internal._assert_task_name_set import _assert_task_name_set
from shell.structure.node.node_task.internal._assert_task_yaml_exists import _assert_task_yaml_exists
from shell.structure.node.node_task.internal._assert_task_md_exists import _assert_task_md_exists
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_node_task(node_task) -> None:
    node_dir = Path.new(node_task._app.cli_.cli_properties_.node_dir_).resolve()
    save_dir = node_dir / DOT_NODE / DIR_TASK

    source_dir = node_task._app.cli_.cli_properties_.source_dir_
    _assert_source_dir_set(source_dir)
    task_name = node_task._app.cli_.cli_properties_.task_name_
    _assert_task_name_set(task_name)
    task_yaml_path = source_dir / f'{task_name}.yaml'
    task_md_path = source_dir / f'{task_name}.md'
    _assert_task_yaml_exists(task_yaml_path)
    _assert_task_md_exists(task_md_path)

    node_task._task_name = task_name
    node_task._task_yaml_file_body = Path.read_text(task_yaml_path)
    node_task._task_md_file_body = Path.read_text(task_md_path)

    dest = Path.new(save_dir)
    Path.mkdir(dest)
    Path.write_text(dest / f'{task_name}.yaml', node_task._task_yaml_file_body)
    Path.write_text(dest / f'{task_name}.md', node_task._task_md_file_body)

```

### platform/shell/structure/node/node_task/node_task.py
```
﻿from shell.utils.path.path import PathType
"""node_task.py
NodeTask: loads task files from task_dir and saves them to the node's task/ folder.

Slots:
    _app                 — parent App
    _task_name           — name of the task derived from the yaml filename (str | None)
    _task_md_file_body   — raw content of <task_name>.md (str | None)
    _task_yaml_file_body — raw content of <task_name>.yaml (str | None)
    _module_status       — ModuleStatus enum; NEW on construction, INIT after init_node_task()
"""

from __future__ import annotations

import yaml

from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_task.internal._init_node_task import _init_node_task
from shell.module.tasker.internal._assert_task_graph_yaml_valid import _assert_task_graph_yaml_valid


class NodeTask:
    """Loads task files from task_dir and saves them to the node's .node/task/ folder."""

    __slots__ = ("_app", "_task_name", "_task_md_file_body", "_task_yaml_file_body", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._task_name: str | None = None
        self._task_md_file_body: str | None = None
        self._task_yaml_file_body: str | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def task_name_(self) -> str | None:
        return self._task_name

    @property
    def task_md_file_body_(self) -> str | None:
        return self._task_md_file_body

    @property
    def task_yaml_file_body_(self) -> str | None:
        return self._task_yaml_file_body

    @property
    def task_graph_dict_(self) -> dict:
        graph_yaml = yaml.safe_load(self._task_yaml_file_body)
        _assert_task_graph_yaml_valid(graph_yaml)
        return graph_yaml

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_task(self) -> None:
        _init_node_task(self)
        self._module_status = ModuleStatus.INIT
```

### platform/shell/structure/node/node_temp/__init__.py
```
```

### platform/shell/structure/node/node_temp/internal/__init__.py
```
```

### platform/shell/structure/node/node_temp/internal/_clean_node_temp.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_temp(node_temp) -> None:
    temp_dir = node_temp.temp_dir_
    if not Path.exists(temp_dir):
        return
    for item in Path.iterdir(temp_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_temp/internal/_init_temp_dir.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TEMP


def _init_temp_dir(node_temp) -> None:
    node_temp._temp_dir = (node_temp._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TEMP).resolve()
    Path.mkdir(node_temp.temp_dir_)
```

### platform/shell/structure/node/node_temp/node_temp.py
```
﻿from shell.utils.path.path import PathType
"""node_temp.py
NodeTemp — temp directory for a single node.

Slots:
    _temp_dir      — path to the temp directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_temp()
"""

from __future__ import annotations


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_temp.internal._init_temp_dir import _init_temp_dir
from shell.structure.node.node_temp.internal._clean_node_temp import _clean_node_temp


class NodeTemp:
    """Manages the temp directory for a single node run."""

    __slots__ = ("_app", "_temp_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._temp_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def temp_dir_(self) -> PathType:
        return self._temp_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_temp(self) -> None:
        _init_temp_dir(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_temp(self) -> None:
        _clean_node_temp(self)
```

### platform/shell/structure/stage/__init__.py
```
﻿from shell.structure.stage.stage.stage import Stage
```

### platform/shell/structure/stage/stage/__init__.py
```
```

### platform/shell/structure/stage/stage/internal/__init__.py
```
```

### platform/shell/structure/stage/stage/internal/_init_stage.py
```
from __future__ import annotations


def _init_stage(stage) -> None:
    stage.stage_active_.init_stage_active()
    stage.stage_pending_.init_stage_pending()
    stage.stage_history_.init_stage_history()
    stage.stage_ignored_.init_stage_ignored()
    stage.stage_dead_.init_stage_dead()
    stage.stage_done_.init_stage_done()
```

### platform/shell/structure/stage/stage/stage.py
```
﻿from shell.utils.path.path import PathType
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
```

### platform/shell/structure/stage/stage_active/__init__.py
```
```

### platform/shell/structure/stage/stage_active/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_active/internal/_clean_stage_active.py
```
﻿from __future__ import annotations

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
﻿from __future__ import annotations


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.utils.path.path import Path, PathType


def _get_stage_active_files(stage_active) -> list[PathType]:
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
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_ACTIVE


def _init_stage_active(stage_active) -> None:
    stage_active._active_dir = stage_active._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_ACTIVE
    Path.mkdir(stage_active.active_dir_)
```

### platform/shell/structure/stage/stage_active/internal/_save_stage_active.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_active(stage_active, file: PathType, dest_name: str | None = None) -> None:
    name = dest_name if dest_name is not None else file.name
    dest = stage_active.active_dir_ / name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_active/stage_active.py
```
﻿from shell.utils.path.path import PathType
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
```

### platform/shell/structure/stage/stage_dead/__init__.py
```
```

### platform/shell/structure/stage/stage_dead/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_dead/internal/_clean_stage_dead.py
```
﻿from __future__ import annotations

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
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_DEAD


def _init_stage_dead(stage_dead) -> None:
    stage_dead._dead_dir = stage_dead._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_DEAD
    Path.mkdir(stage_dead.dead_dir_)
```

### platform/shell/structure/stage/stage_dead/stage_dead.py
```
﻿from shell.utils.path.path import PathType
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
```

### platform/shell/structure/stage/stage_done/__init__.py
```
```

### platform/shell/structure/stage/stage_done/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_done/internal/_clean_stage_done.py
```
﻿from __future__ import annotations

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
﻿from __future__ import annotations


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
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_DONE


def _init_stage_done(stage_done) -> None:
    stage_done._done_dir = stage_done._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_DONE
    Path.mkdir(stage_done.done_dir_)
```

### platform/shell/structure/stage/stage_done/internal/_save_stage_done.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_done(stage_done, file: PathType) -> None:
    dest = stage_done.done_dir_ / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_done/stage_done.py
```
﻿from shell.utils.path.path import PathType
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
```

### platform/shell/structure/stage/stage_history/__init__.py
```
```

### platform/shell/structure/stage/stage_history/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_history/internal/_clean_stage_history.py
```
﻿from __future__ import annotations

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
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_HISTORY


def _init_stage_history(stage_history) -> None:
    stage_history._history_dir = stage_history._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_HISTORY
    Path.mkdir(stage_history.history_dir_)
```

### platform/shell/structure/stage/stage_history/internal/_save_stage_history.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_history(stage_history, file: PathType) -> None:
    dest = stage_history.history_dir_ / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_history/stage_history.py
```
﻿from shell.utils.path.path import PathType
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
```

### platform/shell/structure/stage/stage_ignored/__init__.py
```
```

### platform/shell/structure/stage/stage_ignored/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_ignored/internal/_clean_stage_ignored.py
```
﻿from __future__ import annotations

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
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_IGNORED


def _init_stage_ignored(stage_ignored) -> None:
    stage_ignored._ignored_dir = stage_ignored._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_IGNORED
    Path.mkdir(stage_ignored.ignored_dir_)
```

### platform/shell/structure/stage/stage_ignored/stage_ignored.py
```
﻿from shell.utils.path.path import PathType
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
```

### platform/shell/structure/stage/stage_pending/__init__.py
```
```

### platform/shell/structure/stage/stage_pending/internal/__init__.py
```
```

### platform/shell/structure/stage/stage_pending/internal/_clean_stage_pending.py
```
﻿from __future__ import annotations

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
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _get_stage_pending_files(stage_pending) -> list[PathType]:
    pending_dir = stage_pending.pending_dir_
    if not Path.exists(pending_dir):
        return []
    return [f for f in Path.iterdir(pending_dir) if Path.is_file(f)]
```

### platform/shell/structure/stage/stage_pending/internal/_init_stage_pending.py
```
﻿from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_STAGE, DIR_STAGE_PENDING


def _init_stage_pending(stage_pending) -> None:
    stage_pending._pending_dir = stage_pending._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE / DIR_STAGE_PENDING
    Path.mkdir(stage_pending.pending_dir_)
```

### platform/shell/structure/stage/stage_pending/internal/_save_stage_pending.py
```
﻿from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_stage_pending(stage_pending, file: PathType) -> None:
    dest = stage_pending.pending_dir_ / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/stage/stage_pending/stage_pending.py
```
﻿from shell.utils.path.path import PathType
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
```

### platform/shell/structure/sub_node/__init__.py
```
```

### platform/shell/structure/sub_node/sub_node/internal/__init__.py
```
```

### platform/shell/structure/sub_node/sub_node/internal/_assert_entrypoint_exists.py
```
﻿"""_assert_entrypoint_exists.py
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
﻿"""_assert_node_dir_exists.py
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
﻿from __future__ import annotations

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
﻿"""_run_sub_node.py
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
﻿"""sub_node.py
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
﻿from shell.structure.sub_node.sub_node_command.sub_node_command import SubNodeCommand

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
﻿from shell.utils.path.path import PathType


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
﻿from shell.utils.path.path import Path, PathType
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
﻿"""sub_node_command.py
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
﻿from shell.structure.sub_node.sub_node_properties.sub_node_properties import SubNodeProperties
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
﻿from __future__ import annotations

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
﻿"""sub_node_properties.py
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
﻿"""File.py
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
﻿from shell.utils.path.path import PathType
"""_assert_file_loaded.py
Validate that file has been loaded (file_body is not empty).
"""

from __future__ import annotations



def _assert_file_loaded(file_body: str, file_path: PathType) -> None:
    """Raise ValueError if file_body is empty (file not yet loaded)."""
    if not file_body:
        raise ValueError(f"File not loaded: {file_path}")
```

### platform/shell/utils/file/internal/_assert_suffix_allowed.py
```
﻿from shell.utils.path.path import PathType
"""_assert_suffix_allowed.py
Validate that a file suffix is in the allowed set.
"""

from __future__ import annotations


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
﻿from __future__ import annotations


from shell.utils.file.internal._assert_suffix_allowed import _assert_suffix_allowed
from shell.utils.path.path import Path, PathType


def _read_file(file_path: PathType, encoding: str = "utf-8") -> str:
    _assert_suffix_allowed(file_path)
    return Path.read_text(file_path)
```

### platform/shell/utils/file/internal/_save_file.py
```
﻿from __future__ import annotations


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
﻿from __future__ import annotations

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
