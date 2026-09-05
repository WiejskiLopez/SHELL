"""Command transport port — envelope and delivery protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class CommandDeliveryEnvelope:
    """Technical delivery envelope for commands.

    The channel is encoded by the envelope type, not by a field. ``contract_type``
    is the stable wire contract name and ``destination_service`` is the receiving
    bounded context. ``outbox_id`` is intentionally absent — it is the local
    identity of the sender's outbox record.
    """

    command_id: str
    contract_type: str
    source_service: str
    destination_service: str
    issued_at: datetime
    schema_version: int = 1
    correlation_id: str = ""
    causation_id: str = ""
    payload: dict[str, object] = field(default_factory=dict)


class CommandDeliveryTransport(Protocol):
    """Port for delivering command envelopes to the broker wire."""

    async def deliver(self, envelope: CommandDeliveryEnvelope) -> None: ...