from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class AuthSessionCreatedIntegrationEvent(IntegrationEvent):
    """Public User login contract consumed locally by the Session BC."""

    auth_session_id: str
    user_id: str
