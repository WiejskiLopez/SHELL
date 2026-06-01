"""tasker.py
Tasker: structured runtime state for a single task.

Slots:
    _app          — parent App (DOM back-reference)
    _graph        — Graph instance (built by init_tasker)
    _session_id   — Optional; session timestamp string (YYYYmmdd_HHMMSS)
    _task_record  — Optional; TaskRecord loaded from DB after init_tasker

Validated properties:
    task_dir_              — resolved Path to node directory (task lives there)
    task_name_             — name derived from node directory name
"""

from __future__ import annotations
from shell.structure.graph.graph.graph import Graph
from shell.status.status import Status
from shell.task.task_record import TaskRecord
from shell.module.tasker.internal._assert_session_id_set import _assert_session_id_set
from shell.module.tasker.internal._init_tasker import _init_tasker
from shell.module.tasker.internal._run_tasker import _run_tasker


class Tasker:
    """Structured task data for a shell graph run.

    Constructed lazily and held as app.runner_.tasker_.
    """

    __slots__ = ("_app", "_graph", "_session_id")

    def __init__(self, app) -> None:
        self._app = app
        self._graph: Graph | None = None
        self._session_id: str | None = None

    @property
    def graph_(self) -> Graph:
        """Return the cached Graph instance for this task."""
        if self._graph is None:
            self._graph = Graph(self._app)
        return self._graph

    @property
    def task_name_(self) -> str:
        """Name of the node directory on which this task is executed."""
        return self._app.app_node_.node_.node_dir_.name

    @property
    def session_id_(self) -> str:
        _assert_session_id_set(self._session_id)
        return self._session_id

    @property
    def task_record_(self) -> TaskRecord:
        return self._app.task_record_

    def init_tasker(self, reader=None) -> None:
        _init_tasker(self, reader=reader)

    def run_tasker(self) -> Status:
        return _run_tasker(self)
