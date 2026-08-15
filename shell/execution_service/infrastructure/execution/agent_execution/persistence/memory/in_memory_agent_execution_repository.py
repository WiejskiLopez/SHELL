from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.agent_execution.agent_execution import (
    AgentExecution,
)
from shell.execution_service.domain.execution.aggregates.agent_execution.repositories.agent_execution_repository import (
    AgentExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


class InMemoryAgentExecutionRepository(
    InMemoryRepository[AgentExecution, AgentExecutionId], AgentExecutionRepository
):
    async def get_by_node_execution_id(self, node_id: NodeExecutionId) -> AgentExecution | None:
        for agent in self._store.values():
            if agent.node_execution_id == node_id:
                return copy.deepcopy(agent)
        return None
