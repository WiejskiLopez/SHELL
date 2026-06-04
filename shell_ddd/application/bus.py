"""In-memory CommandBus, QueryBus, EventBus."""
from __future__ import annotations

from typing import Any


class CommandBus:
    """Routes commands to their registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Any], Any] = {}

    def register(self, command_type: type[Any], handler: Any) -> None:
        self._handlers[command_type] = handler

    async def dispatch(self, command: Any) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise KeyError(f"No handler registered for {type(command).__name__}")
        return await handler.handle(command)


class QueryBus:
    """Routes queries to their registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Any], Any] = {}

    def register(self, query_type: type[Any], handler: Any) -> None:
        self._handlers[query_type] = handler

    async def dispatch(self, query: Any) -> Any:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise KeyError(f"No handler registered for {type(query).__name__}")
        return await handler.handle(query)


class EventBus:
    """In-memory event bus — publishes domain events to registered subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[type[Any], list[Any]] = {}

    def subscribe(self, event_type: type[Any], handler: Any) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, events: list[Any]) -> None:
        for event in events:
            for handler in self._subscribers.get(type(event), []):
                await handler.handle(event)
