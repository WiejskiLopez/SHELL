from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.messages import DomainMessage


class MessageHandler(Protocol):
    async def handle(self, message: DomainMessage) -> None: ...
