from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.agent_execution import (
        AgentExecution,
    )
    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class AgentExecutionRepository(Protocol):
    async def get_by_id(self, id_: AgentExecutionId) -> AgentExecution | None: ...

    async def delete(self, id: AgentExecutionId) -> None: ...
    async def exists(self, id: AgentExecutionId) -> ExistsResult: ...

    async def get_by_node_execution_id(self, node_id: NodeExecutionId) -> AgentExecution | None: ...

    async def save(self, agent_execution: AgentExecution) -> None: ...
