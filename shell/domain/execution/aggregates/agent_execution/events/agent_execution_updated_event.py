from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class AgentExecutionUpdatedEvent(DomainEvent):
    agent_execution_id: AgentExecutionId

    @classmethod
    def now(
        cls, agent_execution_id: AgentExecutionId, now: CreatedAt
    ) -> AgentExecutionUpdatedEvent:
        return cls(occurred_at=now, agent_execution_id=agent_execution_id)
