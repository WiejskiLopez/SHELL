from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig
    from shell.domain.definition.value_objects.ids import RunnerConfigId


# TODO: add delete()
# TODO: add exists()
class RunnerConfigRepository(Protocol):
    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None: ...
    async def get_by_package(self, package_name: str) -> RunnerConfig | None: ...
    async def save(self, config: RunnerConfig) -> None: ...
async def delete(self, id: RunnerConfigId) -> None: ...
async def exists(self, id: RunnerConfigId) -> bool: ...
