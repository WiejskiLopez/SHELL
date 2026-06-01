"""graph_node_record.py
GraphNodeRecord — immutable value object representing one row of `graph_node`.

Mirrors the fields previously parsed from `task.yaml` `graph[i]` dict and
populated into SubNodeProperties.
"""

from __future__ import annotations


class GraphNodeRecord:

    __slots__ = (
        "_node_id",
        "_graph_id",
        "_position",
        "_node_dir",
        "_runner_root_dir",
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
        "_status_initial",
        "_extra_json",
    )

    def __init__(
        self,
        node_id: int,
        graph_id: int,
        position: int,
        node_dir: str,
        runner_root_dir: str | None,
        mode: str,
        role: str,
        type: str,
        model: str | None,
        command: str | None,
        timeout: int | None,
        retries: int | None,
        log_level: str | None,
        max_step: int | None,
        no_ask_user: bool | None,
        autopilot: bool | None,
        task_name: str | None,
        source_dir: str | None,
        work_dir: str | None,
        status_initial: str | None,
        extra_json: str | None,
    ) -> None:
        self._node_id = node_id
        self._graph_id = graph_id
        self._position = position
        self._node_dir = node_dir
        self._runner_root_dir = runner_root_dir
        self._mode = mode
        self._role = role
        self._type = type
        self._model = model
        self._command = command
        self._timeout = timeout
        self._retries = retries
        self._log_level = log_level
        self._max_step = max_step
        self._no_ask_user = no_ask_user
        self._autopilot = autopilot
        self._task_name = task_name
        self._source_dir = source_dir
        self._work_dir = work_dir
        self._status_initial = status_initial
        self._extra_json = extra_json

    @property
    def node_id_(self) -> int:
        return self._node_id

    @property
    def graph_id_(self) -> int:
        return self._graph_id

    @property
    def position_(self) -> int:
        return self._position

    @property
    def node_dir_(self) -> str:
        return self._node_dir

    @property
    def runner_root_dir_(self) -> str | None:
        return self._runner_root_dir

    @property
    def mode_(self) -> str:
        return self._mode

    @property
    def role_(self) -> str:
        return self._role

    @property
    def type_(self) -> str:
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

    @property
    def status_initial_(self) -> str | None:
        return self._status_initial

    @property
    def extra_json_(self) -> str | None:
        return self._extra_json
