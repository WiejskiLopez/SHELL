"""DualLayerDispatcher — dispatches inbox/outbox events (scheduler channel)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable


class Inbox(Protocol):
    async def get_communication_events(self, limit: int = 10) -> list[dict[str, Any]]: ...
    async def get_decision_events(self, limit: int = 10) -> list[dict[str, Any]]: ...
    async def mark_processed(self, event_id: str) -> None: ...
    async def is_empty(self) -> bool: ...


class Outbox(Protocol):
    async def publish(self, event: dict[str, Any]) -> None: ...


class DualLayerDispatcher:
    async def dispatch_loop(
        self,
        inbox: Inbox,
        outbox: Outbox,
        handlers: dict[str, Callable[..., Any]],
    ) -> None:
        while True:
            comm_events = await inbox.get_communication_events()
            if comm_events:
                for event in comm_events:
                    handler = handlers.get(event.get("type", ""))
                    if handler:
                        await handler(event, outbox)
                    await inbox.mark_processed(event["id"])
                continue

            decision_events = await inbox.get_decision_events()
            if decision_events:
                for event in decision_events:
                    handler = handlers.get(event.get("type", ""))
                    if handler:
                        await handler(event, outbox)
                    await inbox.mark_processed(event["id"])
                continue

            break
