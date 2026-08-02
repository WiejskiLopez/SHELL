from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.application.bus.message_bus import MessageBus


class MessageBusPublisher:
    """Adapts MessageBus to the MessagePublisher port."""

    def __init__(self, message_bus: MessageBus) -> None:
        self._message_bus = message_bus

    async def publish(self, messages: Sequence[object]) -> None:
        for message in messages:
            await self._message_bus.dispatch(message)
