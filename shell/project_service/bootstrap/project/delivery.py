"""Delivery configuration for the project bounded context.

Przekazuje platformie modele, registry, busy, transporty i sesję delivery —
zgodnie z `outbox_inbox.md` („Docelowe pliki każdego BC"). Moduł nie implementuje
relay, consumerów ani processorów; dostarcza skonsolidowaną konfigurację, którą
kontener przekazuje do fabryk platformy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )


@dataclass(frozen=True, slots=True)
class DeliveryConfig:
    """Skonsolidowana konfiguracja delivery bounded contextu."""

    event_models: Any
    command_models: Any
    event_registry: Mapping[str, type] | None
    command_registry: Mapping[str, type] | None
    event_bus: Any | None
    command_bus: Any | None
    event_transport: Any | None
    command_transport: Any | None
    session_factory: Any


def build_delivery_config(
    *,
    models: PersistenceDeliveryModels,
    event_registry: Mapping[str, type] | None,
    command_registry: Mapping[str, type] | None,
    event_bus: Any | None,
    command_bus: Any | None,
    event_transport: Any | None,
    command_transport: Any | None,
    session_factory: Any,
) -> DeliveryConfig:
    """Build the delivery configuration from the container's delivery inputs."""
    return DeliveryConfig(
        event_models=models.events,
        command_models=models.commands,
        event_registry=event_registry,
        command_registry=command_registry,
        event_bus=event_bus,
        command_bus=command_bus,
        event_transport=event_transport,
        command_transport=command_transport,
        session_factory=session_factory,
    )