from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_skill_execution.value_objects.agent_skill_execution_id import (
        AgentSkillExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class AgentSkillExecutionCreatedEvent(DomainEvent):
    agent_skill_execution_id: AgentSkillExecutionId

    @classmethod
    def now(
        cls,
        agent_skill_execution_id: AgentSkillExecutionId,
        now: CreatedAt,
    ) -> AgentSkillExecutionCreatedEvent:
        return cls(occurred_at=now, agent_skill_execution_id=agent_skill_execution_id)
