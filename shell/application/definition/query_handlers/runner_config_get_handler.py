from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.definition.dto.runner_config import RunnerConfigDto
    from shell.application.definition.queries.runner_config_get_query import RunnerConfigGetQuery
    from shell.application.platform.ports.queries import RunnerConfigQueryService


class RunnerConfigGetHandler:
    def __init__(self, queries: RunnerConfigQueryService) -> None:
        self._queries = queries

    async def handle(self, get_runner_config_query: RunnerConfigGetQuery) -> RunnerConfigDto | None:
        return await self._queries.get_runner_config(get_runner_config_query.package_name)
