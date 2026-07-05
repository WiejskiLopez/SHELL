from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.value_objects.destination import Destination
    from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
    from shell.domain.platform.aggregates.message.value_objects.message_type import MessageType
    from shell.domain.platform.aggregates.message.value_objects.source import Source
    from shell.domain.platform.value_objects.created_at import CreatedAt


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
