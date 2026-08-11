from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class AgentSkillExecutionCreatedIntegrationEvent(IntegrationEvent):
    agent_skill_execution_id: str
