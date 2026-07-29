from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class MessageRouterUpdatedIntegrationEvent(IntegrationEvent):
    message_router_id: str
