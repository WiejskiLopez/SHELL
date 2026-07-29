from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class WorkflowStateChangedIntegrationEvent(IntegrationEvent):
    workflow_id: str
    workflow_state_id: str
