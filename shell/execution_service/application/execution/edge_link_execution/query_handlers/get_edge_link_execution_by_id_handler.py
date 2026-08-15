from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution_service.application.execution.edge_link_execution.dto.edge_link_execution import (
        EdgeLinkExecutionDto,
    )
    from shell.execution_service.application.execution.edge_link_execution.ports.edge_link_execution_query_service import (
        EdgeLinkExecutionQueryService,
    )
    from shell.execution_service.application.execution.edge_link_execution.queries.get_edge_link_execution_by_id_query import (
        GetEdgeLinkExecutionByIdQuery,
    )


class GetEdgeLinkExecutionByIdHandler:
    def __init__(self, queries: EdgeLinkExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetEdgeLinkExecutionByIdQuery) -> EdgeLinkExecutionDto | None:
        return await self._queries.get_by_id(query.edge_link_execution_id)
