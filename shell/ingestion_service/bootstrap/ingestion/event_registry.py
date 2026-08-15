"""Ingestion bounded context event registry."""

from __future__ import annotations

from shell.ingestion_service.bootstrap.ingestion.contract_catalog import INGESTION_CONTRACT_CATALOG
from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.event_registry import (
    build_event_registry,
    discover_event_types,
)


def build_ingestion_event_registry() -> dict[str, type]:
    """Build the event registry owned by the Ingestion bounded context."""
    registry = build_event_registry(
        discover_event_types("shell.ingestion_service.application.ingestion", IntegrationEvent)
    )
    INGESTION_CONTRACT_CATALOG.assert_covers(registry)
    return registry
