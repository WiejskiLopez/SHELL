from __future__ import annotations

from typing import Protocol

from shell.application.definition.dto.runner_config import RunnerConfigDto


class RunnerConfigQueryService(Protocol):
    """Port do pobierania konfiguracji dla runnerów."""

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None: ...
