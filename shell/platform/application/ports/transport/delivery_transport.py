"""Port for transporting serialized delivery records between bounded contexts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from datetime import datetime

DeliveryKind = Literal["event", "message", "command"]


@dataclass(frozen=True)
class DeliveryEnvelope:
    kind: DeliveryKind
    outbox_id: str
    contract_type: str
    occurred_at: datetime
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    event_id: str | None = None
    source_service: str | None = None
    aggregate_id: str | None = None
    aggregate_name: str | None = None
    schema_version: int = 1


class DeliveryTransport(Protocol):
    async def deliver(self, envelope: DeliveryEnvelope) -> None: ...
