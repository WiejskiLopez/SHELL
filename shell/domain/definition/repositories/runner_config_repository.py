from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig
    from shell.domain.platform.value_objects.ids import RunnerConfigId


class RunnerConfigRepository(Protocol):
    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None: ...
    async def get_by_package(self, package_name: str) -> RunnerConfig | None: ...
    async def save(self, config: RunnerConfig) -> None: ...
