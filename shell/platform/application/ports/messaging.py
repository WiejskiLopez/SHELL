from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.events import DomainEvent


class EventPublisher(Protocol):
    async def publish(self, events: list[DomainEvent]) -> None: ...
