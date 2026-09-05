"""Integration-event transport port — envelope and delivery protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class EventDeliveryEnvelope:
    """Technical delivery envelope for integration events.

    The channel is encoded by the envelope type, not by a field. ``contract_type``
    is the stable wire contract name; ``destination_service`` targets the receiving
    bounded context (fan-out events use ``"*"``). ``outbox_id`` is intentionally
    absent — it is the local identity of the sender's outbox record.
    """

    event_id: str
    contract_type: str
    occurred_at: datetime
    aggregate_id: str | None = None
    schema_version: int = 1
    source_service: str | None = None
    destination_service: str | None = None
    correlation_id: str = ""
    causation_id: str = ""
    payload: dict[str, object] = field(default_factory=dict)


class IntegrationEventDeliveryTransport(Protocol):
    """Port for delivering integration-event envelopes to the broker wire."""

    async def deliver(self, envelope: EventDeliveryEnvelope) -> None: ...