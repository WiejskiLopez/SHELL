from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.definition.dto.runner_config import RunnerConfigDto


class RunnerConfigQueryService(Protocol):
    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None: ...
