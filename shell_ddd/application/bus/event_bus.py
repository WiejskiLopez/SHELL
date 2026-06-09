from __future__ import annotations
from typing import Any, Callable


class EventBus:
    """Publikuje zdarzenia domenowe do wielu subskrybentów."""

    def __init__(self) -> None:
        # Zmiana: wartość to lista fabryk [Callable, ...]
        self._handler_factories: dict[type[Any], list[Callable[[], Any]]] = {}

    def subscribe(self, event_type: type[Any], factory: Callable[[], Any]) -> None:
        if event_type not in self._handler_factories:
            self._handler_factories[event_type] = []
        self._handler_factories[event_type].append(factory)

    async def publish(self, events: list[Any]) -> None:
        for event in events:
            factories = self._handler_factories.get(type(event), [])
            for factory in factories:
                # Tworzymy nowego handlera dla każdego subskrybenta
                handler = factory()
                await handler.handle(event)
