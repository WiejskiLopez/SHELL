"""CompositeEventPublisher — fans out to multiple EventPublisher adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.application.ports.ports import EventPublisher
    from shell.platform.domain.events import DomainEvent


class CompositeEventPublisher:
    """Delegates ``publish`` to every publisher in the list, in order."""

    def __init__(self, publishers: list[EventPublisher]) -> None:
        self._publishers = list(publishers)

    async def publish(self, events: list[DomainEvent]) -> None:
        for publisher in self._publishers:
            await publisher.publish(events)
