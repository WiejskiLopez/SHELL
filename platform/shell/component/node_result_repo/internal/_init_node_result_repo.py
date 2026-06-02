from __future__ import annotations

from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.component.node_result_repo.internal._apply_node_result_schema import _apply_node_result_schema


def _init_node_result_repo(repo, driver: SqlDriver) -> None:
    repo._driver = driver
    _apply_node_result_schema(driver)
