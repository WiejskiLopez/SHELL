from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class NodeExecutionStateChangedIntegrationEvent(IntegrationEvent):
    node_execution_id: str
    node_execution_state_id: str
