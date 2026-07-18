from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
        MessageRouterId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class MessageRouterDeletedEvent(DomainEvent):
    messagerouter_id: MessageRouterId

    @classmethod
    def now(cls, messagerouter_id: MessageRouterId, now: CreatedAt) -> MessageRouterDeletedEvent:
        return cls(occurred_at=now, messagerouter_id=messagerouter_id)
