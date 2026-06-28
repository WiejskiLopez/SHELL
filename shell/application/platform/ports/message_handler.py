from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message


class MessageHandler(Protocol):
    async def handle(self, message: Message) -> None: ...
