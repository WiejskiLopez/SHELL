from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.domain.events import DomainEvent


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)
