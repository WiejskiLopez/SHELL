from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.agent_skill_execution.dto.agent_skill_execution import (
        AgentSkillExecutionDto,
    )
    from shell.application.execution.agent_skill_execution.ports.agent_skill_execution_query_service import (
        AgentSkillExecutionQueryService,
    )
    from shell.application.execution.agent_skill_execution.queries.agent_skill_execution_get_by_id_query import (
        AgentSkillExecutionGetByIdQuery,
    )


class AgentSkillExecutionGetByIdHandler:
    def __init__(self, queries: AgentSkillExecutionQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: AgentSkillExecutionGetByIdQuery
    ) -> AgentSkillExecutionDto | None:
        return await self._queries.get_by_id(query.agent_skill_execution_id)
