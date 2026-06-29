from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.aggregates.message.value_objects.destination import Destination
from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
from shell.domain.platform.aggregates.message.value_objects.message_type import MessageType
from shell.domain.platform.aggregates.message.value_objects.source import Source
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class MessageCreatedEvent(DomainEvent):
    message_id: MessageId
    message_type: MessageType
    source: Source
    destination: Destination

    @classmethod
    def now(
        cls,
        message_id: MessageId,
        message_type: MessageType,
        source: Source,
        destination: Destination,
        now: CreatedAt,
    ) -> MessageCreatedEvent:
        return cls(
            occurred_at=now,
            message_id=message_id,
            message_type=message_type,
            source=source,
            destination=destination,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            message_id=MessageId(payload.get("message_id", "")),
            message_type=MessageType(payload.get("message_type", "")),
            source=Source(payload.get("source", "")),
            destination=Destination(payload.get("destination", "")),
        )
