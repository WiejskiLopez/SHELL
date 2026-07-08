from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.agent_execution.dto.agent_execution import (
        AgentExecutionDto,
    )
    from shell.application.execution.agent_execution.ports.agent_execution_query_service import (
        AgentExecutionQueryService,
    )
    from shell.application.execution.agent_execution.queries.agent_execution_get_by_id_query import (
        AgentExecutionGetByIdQuery,
    )


class AgentExecutionGetByIdHandler:
    def __init__(self, queries: AgentExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: AgentExecutionGetByIdQuery) -> AgentExecutionDto | None:
        return await self._queries.get_by_id(query.agent_execution_id)
