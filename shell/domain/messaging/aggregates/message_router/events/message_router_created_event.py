from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId  
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class MessageRouterCreatedEvent(DomainEvent):
    message_id: MessageId

    @classmethod
    def now(
        cls,
        message_id: MessageId,
        now: CreatedAt,
    ) -> MessageRouterCreatedEvent:
        return cls(
            occurred_at=now,
            message_id=message_id,
        )
