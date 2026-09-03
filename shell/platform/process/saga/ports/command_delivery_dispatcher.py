"""CommandDeliveryDispatcher — port dispatch komend delivery.

Dostarczanie komendy do serwisu docelowego odbywa się przez tor delivery
(outbox → inbox, at-least-once). Port należy do warstwy ``process``: komendy
delivery dispatchuje wyłącznie saga / proces manager, nigdy warstwa aplikacji.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.application.commands.command import Command


class CommandDeliveryDispatcher(Protocol):
    """Dispatches a command to its target service through the command outbox.

    Returns the stable ``command_id`` that identifies the intent on the wire.
    """

    async def dispatch(self, command: Command, *, target_service: str) -> str: ...
