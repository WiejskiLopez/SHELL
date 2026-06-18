"""Subscribes to all domain events and logs them for audit purposes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.ports.ports import Logger
    from shell.domain.events.events import DomainEvent


class LogAuditHandler:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def handle(self, event: DomainEvent) -> None:
        self._logger.info(
            "domain_event",
            event_type=type(event).__name__,
            occurred_at=str(event.occurred_at),
        )
