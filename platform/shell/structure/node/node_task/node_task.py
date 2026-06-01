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

from shell.utils.path.path import PathType

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
