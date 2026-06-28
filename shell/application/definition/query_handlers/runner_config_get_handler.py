from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.dto import RunnerConfigDto
    from shell.application.platform.ports.queries import RunnerConfigQueryService
    from shell.application.platform.queries.queries import GetRunnerConfigQuery


class RunnerConfigGetHandler:
    def __init__(self, queries: RunnerConfigQueryService) -> None:
        self._queries = queries

    async def handle(self, get_runner_config_query: GetRunnerConfigQuery) -> RunnerConfigDto | None:
        return await self._queries.get_runner_config(get_runner_config_query.package_name)
