"""Scheduling bounded context event registry."""

from __future__ import annotations

from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.registries.event_registry import (
    build_event_registry,
    discover_event_types,
)
from shell.scheduling_service.bootstrap.scheduling.contract_catalog import (
    SCHEDULING_CONTRACT_CATALOG,
)


def build_scheduling_event_registry() -> dict[str, type]:
    """Build the event registry owned by the Scheduling bounded context."""
    registry = build_event_registry(
        discover_event_types("shell.scheduling_service.application.scheduling", IntegrationEvent)
    )
    SCHEDULING_CONTRACT_CATALOG.assert_covers(registry)
    return registry
