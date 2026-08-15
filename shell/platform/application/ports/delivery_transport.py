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
    delivery_id: str
    delivery_type: str
    occurred_at: datetime
    payload: dict[str, object]
    correlation_id: str
    causation_id: str


class DeliveryTransport(Protocol):
    async def deliver(self, envelope: DeliveryEnvelope) -> None: ...
