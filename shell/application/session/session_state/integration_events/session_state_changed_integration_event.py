from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class SessionStateChangedIntegrationEvent(IntegrationEvent):
    session_id: str
    session_state_id: str
