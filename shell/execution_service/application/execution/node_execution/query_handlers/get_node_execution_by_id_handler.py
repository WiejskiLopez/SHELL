from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution_service.application.execution.node_execution.dto.node_execution_result import (
        NodeExecutionResultDto,
    )
    from shell.execution_service.application.execution.node_execution.ports.node_execution_result_query_service import (
        NodeExecutionResultQueryService,
    )
    from shell.execution_service.application.execution.node_execution.queries.get_node_execution_by_id_query import (
        GetNodeExecutionByIdQuery,
    )


class GetNodeExecutionByIdHandler:
    def __init__(self, queries: NodeExecutionResultQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetNodeExecutionByIdQuery) -> NodeExecutionResultDto | None:
        return await self._queries.get_by_id(query.node_execution_id)
