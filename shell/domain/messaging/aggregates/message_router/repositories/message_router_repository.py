from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
    from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId


class MessageRouterRepository(Protocol):
    async def save(self, message: MessageRouter) -> None: ...

    async def get_by_id(self, message_id: MessageId) -> MessageRouter | None: ...
