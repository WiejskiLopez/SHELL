from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class ProjectStateChangedIntegrationEvent(IntegrationEvent):
    project_id: str
    project_state_id: str
