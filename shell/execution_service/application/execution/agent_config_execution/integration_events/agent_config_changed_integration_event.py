from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class AgentConfigChangedIntegrationEvent(IntegrationEvent):
    agent_config_execution_id: str
