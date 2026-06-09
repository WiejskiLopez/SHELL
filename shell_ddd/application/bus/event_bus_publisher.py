from shell_ddd.application.bus.event_bus import EventBus


class EventBusPublisher:
    """Adapts EventBus to the EventPublisher port."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def publish(self, events: list) -> None:
        await self._event_bus.publish(events)