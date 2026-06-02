from __future__ import annotations

from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.component.node_result_repo.internal._init_node_result_repo import _init_node_result_repo
from shell.component.node_result_repo.internal._save_node_result import _save_node_result


class NodeResultRepo:

    __slots__ = ("_driver",)

    def __init__(self) -> None:
        self._driver: SqlDriver | None = None

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_node_result_repo(self, driver: SqlDriver) -> None:
        _init_node_result_repo(self, driver)

    def save_node_result(
        self,
        workflow_id: str | None = None,
        node_id: str | None = None,
        session_id: str | None = None,
        role: str | None = None,
        mode: str | None = None,
        status: str | None = None,
        returncode: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        started_at: str | None = None,
        stopped_at: str | None = None,
    ) -> int:
        return _save_node_result(
            self, workflow_id, node_id, session_id, role, mode, status,
            returncode, stdout, stderr, started_at, stopped_at,
        )
