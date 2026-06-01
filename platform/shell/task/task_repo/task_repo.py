"""task_repo.py
TaskRepo — DB-backed repository for task definitions and graph topology.

Slots:
    _driver — SqlDriver (None until init_task_repo)
"""

from __future__ import annotations

from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.task.graph_node_record import GraphNodeRecord
from shell.task.task_record import TaskRecord
from shell.task.task_repo.internal._get_current_task import _get_current_task
from shell.task.task_repo.internal._get_graph_nodes import _get_graph_nodes
from shell.task.task_repo.internal._get_task_by_id import _get_task_by_id
from shell.task.task_repo.internal._import_task_files import _import_task_files
from shell.task.task_repo.internal._init_task_repo import _init_task_repo


class TaskRepo:

    __slots__ = ("_driver",)

    def __init__(self) -> None:
        self._driver: SqlDriver | None = None

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_task_repo(self, driver: SqlDriver) -> None:
        _init_task_repo(self, driver)

    def import_task_from_files(
        self,
        name: str,
        source_md_path: str,
        source_yaml_path: str,
    ) -> TaskRecord:
        return _import_task_files(self, name, source_md_path, source_yaml_path)

    def get_current_task(self, name: str) -> TaskRecord | None:
        return _get_current_task(self, name)

    def get_task_by_id(self, task_id: int) -> TaskRecord | None:
        return _get_task_by_id(self, task_id)

    def get_graph_nodes(self, task_id: int) -> list[GraphNodeRecord]:
        return _get_graph_nodes(self, task_id)
