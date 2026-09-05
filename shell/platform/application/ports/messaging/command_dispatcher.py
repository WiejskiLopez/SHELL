"""CommandDispatcher port — hands an inbox command to the local command bus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from shell.platform.application.commands.command import Command


class CommandDispatcher(Protocol):
    """Port used by ``CommandInboxProcessor`` to dispatch a deserialized command.

    The adapter (:class:`shell.platform.application.bus.command_bus_publisher.CommandBusPublisher`)
    forwards to the local :class:`CommandBus`, which routes the command to exactly
    one handler. The transport layer never imports the bus directly.
    """

    async def dispatch(self, command: Command) -> Any: ...