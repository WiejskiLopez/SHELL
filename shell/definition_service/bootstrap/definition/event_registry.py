"""Definition bounded context event registry."""

from __future__ import annotations

from shell.definition_service.bootstrap.definition.contract_catalog import (
    DEFINITION_CONTRACT_CATALOG,
)
from shell.platform.application.events.integration_event import IntegrationEvent
from shell.platform.infrastructure.serialization.event_registry import (
    build_event_registry,
    discover_event_types,
)


def build_definition_event_registry() -> dict[str, type]:
    """Build the event registry owned by the Definition bounded context."""
    event_types = discover_event_types(
        "shell.definition_service.application.definition",
        IntegrationEvent,
    )
    registry = build_event_registry(event_types)
    DEFINITION_CONTRACT_CATALOG.assert_covers(registry)
    return registry
