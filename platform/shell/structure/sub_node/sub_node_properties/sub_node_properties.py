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
