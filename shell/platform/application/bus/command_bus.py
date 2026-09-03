from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.platform.application.command_handlers.command_handler import CommandHandler
    from shell.platform.application.commands.command import Command


class CommandBus:
    """Przesyła komendy do dynamicznie rozwiązanych handlerów."""

    def __init__(self) -> None:
        self._handler_factories: dict[type[Command], Callable[[], CommandHandler[Any]]] = {}

    def register(
        self, command_type: type[Command], factory: Callable[[], CommandHandler[Any]]
    ) -> None:
        if command_type in self._handler_factories:
            raise ValueError(f"Command handler already registered for {command_type.__name__}")
        self._handler_factories[command_type] = factory

    async def dispatch(self, command: Command) -> Any:
        factory = self._handler_factories[type(command)]
        handler = factory()
        return await handler.handle(command)
