from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.definition.runner_config.dto.runner_config import RunnerConfigDto
    from shell.application.definition.runner_config.ports.runner_config_query_service import (
        RunnerConfigQueryService,
    )
    from shell.application.definition.runner_config.queries.runner_config_get_by_id_query import (
        RunnerConfigGetByIdQuery,
    )


class RunnerConfigGetByIdHandler:
    def __init__(self, queries: RunnerConfigQueryService) -> None:
        self._queries = queries

    async def handle(self, query: RunnerConfigGetByIdQuery) -> RunnerConfigDto | None:
        return await self._queries.get_by_id(query.runner_config_id)
