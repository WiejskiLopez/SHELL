from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class MessageBus:
    def __init__(self) -> None:
        self._handler_factories: dict[type[Any], Callable[[], Any]] = {}

    def register(self, message_type: type[Any], factory: Callable[[], Any]) -> None:
        self._handler_factories[message_type] = factory

    async def dispatch(self, message: Any) -> None:
        factory = self._handler_factories[type(message)]
        handler = factory()
        await handler.handle(message)
