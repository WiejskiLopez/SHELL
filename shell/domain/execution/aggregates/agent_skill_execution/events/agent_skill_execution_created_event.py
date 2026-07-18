from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.agentskillexecution.aggregates.agentskillexecution.value_objects.AgentSkillExecutionId import AgentSkillExecutionId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class AgentSkillExecutionCreatedEvent(DomainEvent):
    agentskillexecution_id: AgentSkillExecutionId

    @classmethod
    def now(cls, agentskillexecution_id: AgentSkillExecutionId, now: CreatedAt) -> "AgentSkillExecutionCreatedEvent":
        return cls(occurred_at=now, agentskillexecution_id=agentskillexecution_id)
