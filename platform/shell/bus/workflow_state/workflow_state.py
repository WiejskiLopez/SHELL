"""workflow_state.py
WorkflowState — facade for workflow + node_state tables.

Slots:
    _driver — SqlDriver (None until init_workflow_state)
"""

from __future__ import annotations

from shell.bus.workflow_state.internal._close_workflow import _close_workflow
from shell.bus.workflow_state.internal._get_workflow import _get_workflow, _list_node_states
from shell.bus.workflow_state.internal._open_workflow import _open_workflow
from shell.bus.workflow_state.internal._set_node_status import _set_node_status
from shell.memory.sql_driver.sql_driver import SqlDriver


class WorkflowState:
    """Facade exposing workflow + node_state tables."""

    __slots__ = ("_driver",)

    def __init__(self) -> None:
        self._driver: SqlDriver | None = None

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_workflow_state(self, driver: SqlDriver) -> None:
        self._driver = driver

    def open_workflow(
        self,
        workflow_id: str,
        root_task_id: str | None = None,
        parent_workflow_id: str | None = None,
        task_id: int | None = None,
        session_id: str | None = None,
    ) -> None:
        _open_workflow(self, workflow_id, root_task_id, parent_workflow_id, task_id, session_id)

    def close_workflow(self, workflow_id: str, status: str = "COMPLETED") -> None:
        _close_workflow(self, workflow_id, status)

    def set_node_status(
        self,
        workflow_id: str,
        node_id: str,
        role: str | None,
        current_status: str,
        last_envelope_id: int | None = None,
    ) -> None:
        _set_node_status(self, workflow_id, node_id, role, current_status, last_envelope_id)

    def get_workflow(self, workflow_id: str) -> dict | None:
        return _get_workflow(self, workflow_id)

    def list_node_states(self, workflow_id: str) -> list[dict]:
        return _list_node_states(self, workflow_id)
