"""EventHandler — klasa bazowa handlerów eventów (integracja/subskrypcja).

``EventHandler[TEvent]`` jest generyczną klasą bazową, po której dziedziczą
handlery eventów SHELL (np. ``AuthSessionCreatedEventHandler``). Umożliwia:
- ścisłe typowanie rejestracji subskrybentów w ``EventBus`` na
  ``Callable[[], EventHandler]`` — myPy wymusi, że subskrybowany jest tylko
  handler eventu;
- wywołanie ``handler.handle(event)`` z poprawnie wpisanym eventem.

Wstrzykiwanie zależności odbywa się przez ``__init__`` (handlery bezstanowe).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TEvent = TypeVar("TEvent")


class EventHandler(ABC, Generic[TEvent]):
    """Znacznik handlera eventu — abstrakcyjny kontrakt ``handle(event)``."""

    __slots__ = ()

    @abstractmethod
    async def handle(self, event: TEvent) -> None:
        raise NotImplementedError
