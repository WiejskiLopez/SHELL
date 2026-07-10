from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.application.bus.event_bus import EventBus
    from shell.platform.domain.events import DomainEvent


class EventBusPublisher:
    """Adapts EventBus to the EventPublisher port."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def publish(self, events: list[DomainEvent]) -> None:
        await self._event_bus.publish(events)
