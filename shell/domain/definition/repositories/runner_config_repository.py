from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig
    from shell.domain.definition.value_objects.ids import RunnerConfigId
    from shell.domain.definition.value_objects.package_name import PackageName
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class RunnerConfigRepository(Protocol):
    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None: ...
    async def get_by_package(self, package_name: PackageName) -> RunnerConfig | None: ...
    async def save(self, config: RunnerConfig) -> None: ...
    async def delete(self, id: RunnerConfigId) -> None: ...
    async def exists(self, id: RunnerConfigId) -> ExistsResult: ...
