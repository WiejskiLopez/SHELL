from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter


class MessageHandler(Protocol):
    async def handle(self, message: MessageRouter) -> None: ...
