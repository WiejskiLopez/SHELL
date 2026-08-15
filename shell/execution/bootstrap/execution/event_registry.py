"""Execution bounded context event registry."""

from __future__ import annotations

from shell.execution.bootstrap.execution.contract_catalog import EXECUTION_CONTRACT_CATALOG
from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.serialization.event_registry import (
    build_event_registry,
    discover_event_types,
)


def build_execution_event_registry() -> dict[str, type]:
    """Build the event registry owned by the Execution bounded context."""
    registry = build_event_registry(
        discover_event_types("shell.execution.application.execution", IntegrationEvent)
    )
    EXECUTION_CONTRACT_CATALOG.assert_covers(registry)
    return registry
