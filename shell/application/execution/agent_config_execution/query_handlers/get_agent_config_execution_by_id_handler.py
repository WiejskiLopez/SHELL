from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.agent_config_execution.dto.agent_config_execution import (
        AgentConfigExecutionDto,
    )
    from shell.application.execution.agent_config_execution.ports.agent_config_execution_query_service import (
        AgentConfigExecutionQueryService,
    )
    from shell.application.execution.agent_config_execution.queries.get_agent_config_execution_by_id_query import (
        GetAgentConfigExecutionByIdQuery,
    )


class GetAgentConfigExecutionByIdHandler:
    def __init__(self, queries: AgentConfigExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: GetAgentConfigExecutionByIdQuery
    ) -> AgentConfigExecutionDto | None:
        return await self._queries.get_by_id(query.agent_config_execution_id)
