from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.agent_execution.repositories.agent_execution_repository import (
    AgentExecutionRepository,
)
from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.agent_execution import (
        AgentExecution,
    )


class InMemoryAgentExecutionRepository(AgentExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, AgentExecution] = {}

    async def get_by_id(self, id_: AgentExecutionId) -> AgentExecution | None:
        agent = self._store.get(id_.value)
        return copy.deepcopy(agent) if agent is not None else None

    async def get_by_node_execution_id(
        self, node_id: GraphNodeExecutionId
    ) -> AgentExecution | None:
        for agent in self._store.values():
            if agent.graph_node_execution_id == node_id:
                return copy.deepcopy(agent)
        return None

    async def save(self, agent_execution: AgentExecution) -> None:
        self._store[agent_execution.id.value] = copy.deepcopy(agent_execution)
