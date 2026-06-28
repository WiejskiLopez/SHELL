from __future__ import annotations

import copy

from shell.domain.execution.aggregates.agent_execution.repositories.agent_execution_repository import (
    AgentExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.agent_execution.agent_execution import (
    AgentExecution,
)
from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryAgentExecutionRepository(InMemoryRepository[AgentExecution, AgentExecutionId], AgentExecutionRepository):

    async def get_by_node_execution_id(
        self, node_id: GraphNodeExecutionId
    ) -> AgentExecution | None:
        for agent in self._store.values():
            if agent.graph_node_execution_id == node_id:
                return copy.deepcopy(agent)
        return None
