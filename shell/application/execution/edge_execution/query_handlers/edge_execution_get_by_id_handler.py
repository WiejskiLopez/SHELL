from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.edge_execution.dto.edge_execution import EdgeExecutionDto
    from shell.application.execution.edge_execution.ports.edge_execution_query_service import (
        EdgeExecutionQueryService,
    )
    from shell.application.execution.edge_execution.queries.edge_execution_get_by_id_query import (
        EdgeExecutionGetByIdQuery,
    )


class EdgeExecutionGetByIdHandler:
    def __init__(self, queries: EdgeExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: EdgeExecutionGetByIdQuery) -> EdgeExecutionDto | None:
        return await self._queries.get_by_id(query.edge_execution_id)
