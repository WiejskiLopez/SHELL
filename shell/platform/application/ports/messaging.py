from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence


class EventPublisher(Protocol):
    async def publish(self, events: Sequence[object]) -> None: ...


class MessagePublisher(Protocol):
    async def publish(self, messages: Sequence[object]) -> None: ...
