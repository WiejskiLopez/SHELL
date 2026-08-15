"""User bounded context event registry."""

from __future__ import annotations

from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.event_registry import (
    build_event_registry,
    discover_event_types,
)
from shell.user.bootstrap.user.contract_catalog import USER_CONTRACT_CATALOG


def build_user_event_registry() -> dict[str, type]:
    """Build the event registry owned by the User bounded context."""
    registry = build_event_registry(
        discover_event_types("shell.user.application.user", IntegrationEvent)
    )
    USER_CONTRACT_CATALOG.assert_covers(registry)
    return registry
