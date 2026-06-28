from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.domain.execution.aggregates.agent_skill_execution.repositories.agent_skill_execution_repository import (
    AgentSkillExecutionRepository,
)
from shell.domain.execution.aggregates.agent_skill_execution.value_objects.agent_skill_execution_id import (
    AgentSkillExecutionId,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_skill_execution.agent_skill_execution import (
        AgentSkillExecution,
    )


class InMemoryAgentSkillExecutionRepository(AgentSkillExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, AgentSkillExecution] = {}

    async def get_by_id(self, id_: AgentSkillExecutionId) -> AgentSkillExecution | None:
        item = self._store.get(id_.value)
        return copy.deepcopy(item) if item is not None else None

    async def list_by_agent_execution_id(
        self, agent_execution_id: AgentExecutionId
    ) -> list[AgentSkillExecution]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.agent_execution_id == agent_execution_id
        ]

    async def save(self, agent_skill_execution: AgentSkillExecution) -> None:
        self._store[agent_skill_execution.id.value] = copy.deepcopy(agent_skill_execution)

    async def delete(self, id_: AgentSkillExecutionId) -> None:
        self._store.pop(id_.value, None)

    async def exists(self, id_: AgentSkillExecutionId) -> bool:
        return id_.value in self._store
