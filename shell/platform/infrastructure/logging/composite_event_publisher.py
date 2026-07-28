"""CompositeEventPublisher — fans out to multiple EventPublisher adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.application.ports.ports import EventPublisher


class CompositeEventPublisher:
    """Delegates ``publish`` to every publisher in the list, in order."""

    def __init__(self, publishers: list[EventPublisher]) -> None:
        self._publishers = list(publishers)

    async def publish(self, events: Sequence[object]) -> None:
        for publisher in self._publishers:
            await publisher.publish(events)
