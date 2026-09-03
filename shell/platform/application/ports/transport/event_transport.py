"""Integration-event transport port — envelope and delivery protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class IntegrationEventDeliveryEnvelope:
    kind: Literal["event"]
    outbox_id: str
    integration_event_name: str
    occurred_at: datetime
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    schema_version: int = 1
    event_id: str | None = None
    source_service: str | None = None
    aggregate_id: str | None = None


class IntegrationEventDeliveryTransport(Protocol):
    """Port for delivering integration-event envelopes to the broker wire."""

    async def deliver(self, envelope: IntegrationEventDeliveryEnvelope) -> None: ...