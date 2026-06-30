from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.domain.scheduling.services.pending_graph_finder import (
        GraphExecutionRepository as PendingGraphRepo,
    )
    from shell.domain.scheduling.services.pending_graph_finder import (
        PendingGraphFinder,
    )


class Inbox(Protocol):
    async def get_communication_events(self, limit: int = 10) -> list[dict[str, Any]]: ...
    async def get_decision_events(self, limit: int = 10) -> list[dict[str, Any]]: ...
    async def mark_processed(self, event_id: str) -> None: ...
    async def is_empty(self) -> bool: ...


class Outbox(Protocol):
    async def publish(self, event: dict[str, Any]) -> None: ...


class DualLayerDispatcher:
    def __init__(
        self,
        pending_graph_finder: PendingGraphFinder | None = None,
        graph_execution_repository: PendingGraphRepo | None = None,
    ) -> None:
        self._pending_graph_finder = pending_graph_finder
        self._graph_execution_repository = graph_execution_repository

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

            if (
                self._pending_graph_finder is not None
                and self._graph_execution_repository is not None
            ):
                graph = await self._pending_graph_finder.find_next(self._graph_execution_repository)
                if graph is not None:
                    handler = handlers.get("graph_pending")
                    if handler:
                        await handler(graph, outbox)
                    continue

            break
