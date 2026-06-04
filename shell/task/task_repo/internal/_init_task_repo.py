from __future__ import annotations

from typing import TYPE_CHECKING

from shell.task.task_schema.internal._apply_task_schema import _apply_task_schema

if TYPE_CHECKING:
    from shell.memory.sql_driver.sql_driver import SqlDriver
    from shell.task.task_repo.task_repo import TaskRepo


def _init_task_repo(repo: TaskRepo, driver: SqlDriver) -> None:
    repo._driver = driver
    _apply_task_schema(driver)
