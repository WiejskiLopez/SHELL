from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.agent_skill_execution.dto.agent_skill_execution import (
        AgentSkillExecutionDto,
    )


class AgentSkillExecutionQueryService(Protocol):
    async def get_by_id(
        self, agent_skill_execution_id: str
    ) -> AgentSkillExecutionDto | None: ...
