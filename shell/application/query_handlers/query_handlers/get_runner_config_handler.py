from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.dto import RunnerConfigDto
    from shell.application.ports.queries import RunnerConfigQueryService
    from shell.application.queries.queries import GetRunnerConfigQuery


class GetRunnerConfigHandler:
    def __init__(self, queries: RunnerConfigQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetRunnerConfigQuery) -> RunnerConfigDto | None:
        return await self._queries.get_runner_config(query.package_name)
