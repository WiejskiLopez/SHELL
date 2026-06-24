from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import AgentExecutionId
from shell.domain.execution.aggregates.agent_execution.value_objects.agent_skill_execution_id import (
    AgentSkillExecutionId,
)
from shell.domain.execution.value_objects.skill_payload import SkillPayload

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class AgentSkillExecution:
    id: AgentSkillExecutionId
    agent_execution_id: AgentExecutionId
    payload: SkillPayload
    created_at: datetime
