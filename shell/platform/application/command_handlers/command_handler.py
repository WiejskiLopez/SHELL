"""CommandHandler — klasa bazowa handlerów komend aplikacyjnych.

``CommandHandler[TCommand]`` jest generyczną klasą bazową, po której dziedziczą
wszystkie handlery komend SHELL (np. ``CreateProjectHandler(CommandHandler[CreateProjectCommand])``).
Umożliwia:
- ścisłe typowanie rejestru ``CommandBus`` na ``Callable[[], CommandHandler]`` —
  myPy wymusi, że rejestrowany jest tylko handler komendy;
- wywołanie ``handler.handle(command)`` z poprawnie wpisaną komendą (bez rzutowań).

Wstrzykiwanie zależności odbywa się przez ``__init__`` (handlery są bezstanowe —
patrz ``test_handlers_are_stateless``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from shell.platform.application.commands.command import Command

TCommand = TypeVar("TCommand", bound="Command")


class CommandHandler(ABC, Generic[TCommand]):
    """Znacznik handlera komendy — abstrakcyjny kontrakt ``handle(command)``."""

    __slots__ = ()

    @abstractmethod
    async def handle(self, command: TCommand) -> Any:
        raise NotImplementedError
