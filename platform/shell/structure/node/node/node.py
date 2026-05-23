"""node.py
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



