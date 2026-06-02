from __future__ import annotations

from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.component.runner_config_repo.internal._init_runner_config_repo import _init_runner_config_repo
from shell.component.runner_config_repo.internal._import_runner_config import (
    _import_runner_config_if_changed,
    _get_current_runner_config,
)
from shell.component.runner_config_repo.internal._bootstrap_runner_config import (
    _bootstrap_runner_config,
    _get_runner_config_body,
)
from shell.utils.path.path import PathType


class RunnerConfigRepo:

    __slots__ = ("_driver",)

    def __init__(self) -> None:
        self._driver: SqlDriver | None = None

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_runner_config_repo(self, driver: SqlDriver) -> None:
        _init_runner_config_repo(self, driver)

    def import_runner_config_if_changed(
        self,
        package_name: str,
        kind: str,
        body: str,
        source_uri: str | None = None,
    ) -> dict:
        return _import_runner_config_if_changed(self, package_name, kind, body, source_uri)

    def get_current_runner_config(self, package_name: str, kind: str) -> dict | None:
        return _get_current_runner_config(self, package_name, kind)

    def bootstrap_runner_config(self, package_name: str, kind: str, yaml_path: PathType) -> str:
        return _bootstrap_runner_config(self, package_name, kind, yaml_path)

    def get_runner_config_body(self, package_name: str, kind: str) -> str:
        return _get_runner_config_body(self, package_name, kind)
