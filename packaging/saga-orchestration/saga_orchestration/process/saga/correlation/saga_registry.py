from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from saga_orchestration.process.saga.correlation.event_route import EventRoute


class SagaRegistry:
    __slots__ = ("_routes",)

    def __init__(self) -> None:
        self._routes: dict[type[object], list[EventRoute]] = {}

    def register(self, event_type: type[object], route: EventRoute) -> None:
        routes = self._routes.setdefault(event_type, [])
        if any(existing.saga_type == route.saga_type for existing in routes):
            raise ValueError(f"Duplicate saga route for {event_type.__name__}: {route.saga_type!r}")
        routes.append(route)

    def routes_for(self, event_type: type[object]) -> Sequence[EventRoute]:
        return list(self._routes.get(event_type, ()))

    def route_for(self, event_type: type[object], saga_type: str) -> EventRoute | None:
        return next(
            (route for route in self._routes.get(event_type, ()) if route.saga_type == saga_type),
            None,
        )
