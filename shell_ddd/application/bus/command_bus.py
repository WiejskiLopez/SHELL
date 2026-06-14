from __future__ import annotations

from collections.abc import Callable
from typing import Any


class CommandBus:
    """Przesyła komendy do dynamicznie rozwiązanych handlerów."""

    def __init__(self) -> None:
        self._handler_factories: dict[type[Any], Callable[[], Any]] = {}

    def register(self, command_type: type[Any], factory: Callable[[], Any]) -> None:
        self._handler_factories[command_type] = factory

    async def dispatch(self, command: Any) -> Any:
        factory = self._handler_factories[type(command)]
        handler = factory()
        return await handler.handle(command)
