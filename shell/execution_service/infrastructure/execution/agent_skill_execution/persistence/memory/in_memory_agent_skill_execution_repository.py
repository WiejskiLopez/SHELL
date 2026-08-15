from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.agent_skill_execution.agent_skill_execution import (
    AgentSkillExecution,
)
from shell.execution_service.domain.execution.aggregates.agent_skill_execution.repositories.agent_skill_execution_repository import (
    AgentSkillExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.agent_skill_execution.value_objects.agent_skill_execution_id import (
    AgentSkillExecutionId,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )


class InMemoryAgentSkillExecutionRepository(
    InMemoryRepository[AgentSkillExecution, AgentSkillExecutionId], AgentSkillExecutionRepository
):
    async def list_by_agent_execution_id(
        self, agent_execution_id: AgentExecutionId
    ) -> list[AgentSkillExecution]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.agent_execution_id == agent_execution_id
        ]

    async def exists(self, id_: AgentSkillExecutionId) -> ExistsResult:
        return ExistsResult(id_.value in self._store)
