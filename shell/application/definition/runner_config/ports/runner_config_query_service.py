from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.definition.runner_config.dto.runner_config import RunnerConfigDto


class RunnerConfigQueryService(Protocol):
    async def get_by_id(self, runner_config_id: str) -> RunnerConfigDto | None: ...
