from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
        AgentConfigExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class AgentConfigExecutionDeletedEvent(DomainEvent):
    agent_config_execution_id: AgentConfigExecutionId

    @classmethod
    def now(
        cls, agent_config_execution_id: AgentConfigExecutionId, now: CreatedAt
    ) -> AgentConfigExecutionDeletedEvent:
        return cls(occurred_at=now, agent_config_execution_id=agent_config_execution_id)
