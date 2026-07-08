from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.domain.messaging.aggregates.message.message import Message


class MessageBus:
    def __init__(self) -> None:
        self._handler_factories: dict[str, list[Callable[[], Any]]] = {}

    def subscribe(self, message_type: str, factory: Callable[[], Any]) -> None:
        if message_type not in self._handler_factories:
            self._handler_factories[message_type] = []
        self._handler_factories[message_type].append(factory)

    async def dispatch(self, events: list[Message]) -> None:
        for message in events:
            factories = self._handler_factories.get(message.message_type.value, [])
            for factory in factories:
                handler = factory()
                await handler.handle(message)
