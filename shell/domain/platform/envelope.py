"""Envelope — techniczna koperta transportowa dla Message.

Envelope NIE jest agregatem. Jest transientną strukturą danych używaną
do zapakowania Message przed wysłaniem do outbox_message i rozpakowania
po stronie odbiorcy. Nie posiada własnej tabeli, repozytorium, eventów.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message


@dataclass(frozen=True, slots=True)
class Envelope:
    envelope_id: str
    message_id: str
    trace_id: str
    sender_service: str
    receiver_service: str
    transport_metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_message(
        cls,
        message: Message,
        trace_id: str,
        sender_service: str,
        receiver_service: str,
        transport_metadata: dict[str, object] | None = None,
        correlation_id: str | None = None,
    ) -> Envelope:
        import uuid

        metadata = dict(transport_metadata or {})
        if correlation_id is not None:
            metadata["correlation_id"] = correlation_id

        return cls(
            envelope_id=str(uuid.uuid4()),
            message_id=message.id.value,
            trace_id=trace_id,
            sender_service=sender_service,
            receiver_service=receiver_service,
            transport_metadata=metadata,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "envelope_id": self.envelope_id,
            "message_id": self.message_id,
            "trace_id": self.trace_id,
            "sender_service": self.sender_service,
            "receiver_service": self.receiver_service,
            "transport_metadata": dict(self.transport_metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Envelope:
        return cls(
            envelope_id=str(data.get("envelope_id", "")),
            message_id=str(data.get("message_id", "")),
            trace_id=str(data.get("trace_id", "")),
            sender_service=str(data.get("sender_service", "")),
            receiver_service=str(data.get("receiver_service", "")),
            transport_metadata=dict(data.get("transport_metadata", {}) or {}),
        )
