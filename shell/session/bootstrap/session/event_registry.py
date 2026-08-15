"""Session bounded context event registry.

Owns the Session BC integration events and explicitly lists cross-BC events that
the Session BC consumes (here: the User BC login event that triggers session
opening). Only these two sources are allowed — no arbitrary cross-BC discovery.
"""

from __future__ import annotations

from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.event_registry import (
    build_event_registry,
    discover_event_types,
)
from shell.session.bootstrap.session.contract_catalog import SESSION_CONTRACT_CATALOG
from shell.user.application.user.auth_session.integration_events.auth_session_created_integration_event import (
    AuthSessionCreatedIntegrationEvent,
)


def build_session_event_registry() -> dict[str, type]:
    """Build the event registry owned by the Session bounded context.

    Includes the Session BC's own integration events plus the explicitly consumed
    ``AuthSessionCreatedIntegrationEvent`` from the User BC.
    """
    owned = discover_event_types("shell.session.application.session", IntegrationEvent)
    consumed: tuple[type, ...] = (AuthSessionCreatedIntegrationEvent,)
    registry = build_event_registry((*owned, *consumed))
    SESSION_CONTRACT_CATALOG.assert_covers(registry)
    return registry
