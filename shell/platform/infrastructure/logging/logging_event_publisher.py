"""LoggingEventPublisher — publishes domain events via the Logger port."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.platform.application.ports.ports import Logger


class LoggingEventPublisher:
    """EventPublisher adapter that logs each domain event as a structured JSON entry."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def publish(self, events: Sequence[object]) -> None:
        for event in events:
            self._logger.info(
                "domain_event",
                event_type=type(event).__name__,
                occurred_at=event.occurred_at.value.isoformat(),  # type: ignore[attr-defined]
            )
