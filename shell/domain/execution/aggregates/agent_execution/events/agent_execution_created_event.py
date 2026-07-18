from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.value_objects.AgentExecutionId import AgentExecutionId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class AgentExecutionCreatedEvent(DomainEvent):
    agentexecution_id: AgentExecutionId

    @classmethod
    def now(cls, agentexecution_id: AgentExecutionId, now: CreatedAt) -> "AgentExecutionCreatedEvent":
        return cls(occurred_at=now, agentexecution_id=agentexecution_id)
