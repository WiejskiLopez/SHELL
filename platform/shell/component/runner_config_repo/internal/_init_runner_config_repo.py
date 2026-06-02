from __future__ import annotations

from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.component.runner_config_repo.internal._apply_runner_config_schema import _apply_runner_config_schema


def _init_runner_config_repo(repo, driver: SqlDriver) -> None:
    repo._driver = driver
    _apply_runner_config_schema(driver)
