from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.runner_config.runner_config import (
        RunnerConfig,
    )
    from shell.definition_service.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
        RunnerConfigId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class RunnerConfigRepository(Protocol):
    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None: ...
    async def save(self, config: RunnerConfig) -> None: ...
    async def delete(self, id: RunnerConfigId) -> None: ...
    async def exists(self, id: RunnerConfigId) -> ExistsResult: ...
