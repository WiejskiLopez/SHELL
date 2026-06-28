from __future__ import annotations

from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.definition.value_objects.ids import (
    RunnerConfigId,
)
from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.package_name import PackageName
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryRunnerConfigRepository(InMemoryRepository[RunnerConfig, RunnerConfigId], RunnerConfigRepository):

    async def get_by_package(self, package_name: PackageName) -> RunnerConfig | None:
        for runner_config in self._store.values():
            if runner_config.package_name == package_name:
                return runner_config
        return None
