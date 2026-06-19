from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.platform.value_objects.ids import RunnerConfigId

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig


class InMemoryRunnerConfigRepository(RunnerConfigRepository):
    def __init__(self) -> None:
        self._store: dict[str, RunnerConfig] = {}

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        return self._store.get(config_id.value)

    async def get_by_package(self, package_name: str) -> RunnerConfig | None:
        for runner_config in self._store.values():
            if runner_config.package_name == package_name:
                return runner_config
        return None

    async def save(self, config: RunnerConfig) -> None:
        self._store[config.id.value] = config
