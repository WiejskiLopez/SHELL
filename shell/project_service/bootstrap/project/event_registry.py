"""Project bounded context event registry."""

from __future__ import annotations

from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.registries.event_registry import (
    build_event_registry,
    discover_event_types,
)
from shell.project_service.bootstrap.project.contract_catalog import PROJECT_CONTRACT_CATALOG


def build_project_event_registry() -> dict[str, type]:
    """Build the event registry owned by the Project bounded context."""
    registry = build_event_registry(
        discover_event_types("shell.project_service.application.project", IntegrationEvent)
    )
    PROJECT_CONTRACT_CATALOG.assert_covers(registry)
    return registry
