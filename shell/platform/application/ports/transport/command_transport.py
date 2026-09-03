"""Command transport port — envelope and delivery protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class CommandDeliveryEnvelope:
    kind: Literal["command"]
    outbox_id: str
    command_id: str
    command_name: str
    source_service: str
    target_service: str
    issued_at: datetime
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    schema_version: int = 1


class CommandDeliveryTransport(Protocol):
    """Port for delivering command envelopes to the broker wire."""

    async def deliver(self, envelope: CommandDeliveryEnvelope) -> None: ...