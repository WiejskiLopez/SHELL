from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.scheduling.scheduler_definition.dto.scheduler_definition import (
        SchedulerDefinitionDto,
    )
    from shell.application.scheduling.scheduler_definition.ports.scheduler_definition_query_service import (
        SchedulerDefinitionQueryService,
    )
    from shell.application.scheduling.scheduler_definition.queries.scheduler_definition_get_by_id_query import (
        SchedulerDefinitionGetByIdQuery,
    )


class SchedulerDefinitionGetByIdHandler:
    def __init__(self, queries: SchedulerDefinitionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: SchedulerDefinitionGetByIdQuery
    ) -> SchedulerDefinitionDto | None:
        return await self._queries.get_by_id(query.scheduler_definition_id)
