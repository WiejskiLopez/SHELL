from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.node_execution.dto.node_execution_result import (
        NodeExecutionResultDto,
    )
    from shell.application.execution.node_execution.ports.node_execution_result_query_service import (
        NodeExecutionResultQueryService,
    )
    from shell.application.execution.node_execution.queries.node_execution_get_by_id_query import (
        NodeExecutionGetByIdQuery,
    )


class NodeExecutionGetByIdHandler:
    def __init__(self, queries: NodeExecutionResultQueryService) -> None:
        self._queries = queries

    async def handle(self, query: NodeExecutionGetByIdQuery) -> NodeExecutionResultDto | None:
        return await self._queries.get_by_id(query.node_execution_id)
