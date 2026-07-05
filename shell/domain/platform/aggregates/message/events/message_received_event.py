from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
    from shell.domain.platform.aggregates.message.value_objects.message_status import MessageStatus
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class MessageReceivedEvent(DomainEvent):
    message_id: MessageId
    previous_status: MessageStatus
    new_status: MessageStatus

    @classmethod
    def now(
        cls,
        message_id: MessageId,
        previous_status: MessageStatus,
        new_status: MessageStatus,
        now: CreatedAt,
    ) -> MessageReceivedEvent:
        return cls(
            occurred_at=now,
            message_id=message_id,
            previous_status=previous_status,
            new_status=new_status,
        )
