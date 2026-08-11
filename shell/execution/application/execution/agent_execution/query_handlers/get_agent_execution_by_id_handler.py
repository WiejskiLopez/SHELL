from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution.application.execution.agent_execution.dto.agent_execution import (
        AgentExecutionDto,
    )
    from shell.execution.application.execution.agent_execution.ports.agent_execution_query_service import (
        AgentExecutionQueryService,
    )
    from shell.execution.application.execution.agent_execution.queries.get_agent_execution_by_id_query import (
        GetAgentExecutionByIdQuery,
    )


class GetAgentExecutionByIdHandler:
    def __init__(self, queries: AgentExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetAgentExecutionByIdQuery) -> AgentExecutionDto | None:
        return await self._queries.get_by_id(query.agent_execution_id)
