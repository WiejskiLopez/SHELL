from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
        MessageRouterId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class MessageRouterCreatedEvent(DomainEvent):
    message_router_id: MessageRouterId

    @classmethod
    def now(
        cls,
        message_router_id: MessageRouterId,
        now: OccurredAt,
    ) -> MessageRouterCreatedEvent:
        return cls(
            occurred_at=now,
            message_router_id=message_router_id,
        )
