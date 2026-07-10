from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.domain.execution.aggregates.agent_skill_execution.agent_skill_execution import (
        AgentSkillExecution,
    )
    from shell.domain.execution.aggregates.agent_skill_execution.value_objects.agent_skill_execution_id import (
        AgentSkillExecutionId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class AgentSkillExecutionRepository(Protocol):
    async def get_by_id(self, id_: AgentSkillExecutionId) -> AgentSkillExecution | None: ...

    async def list_by_agent_execution_id(
        self, agent_execution_id: AgentExecutionId
    ) -> list[AgentSkillExecution]: ...

    async def save(self, agent_skill_execution: AgentSkillExecution) -> None: ...

    async def delete(self, id_: AgentSkillExecutionId) -> None: ...

    async def exists(self, id_: AgentSkillExecutionId) -> ExistsResult: ...
