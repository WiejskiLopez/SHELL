"""CommandBusPublisher — adapts CommandBus to the CommandDispatcher port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.commands.command import Command


class CommandBusPublisher:
    """Adapts :class:`CommandBus` to the :class:`CommandDispatcher` port.

    Used by ``CommandInboxProcessor`` so the transport layer depends on the port,
    not on the application bus.
    """

    def __init__(self, command_bus: CommandBus) -> None:
        self._command_bus = command_bus

    async def dispatch(self, command: Command) -> Any:
        return await self._command_bus.dispatch(command)