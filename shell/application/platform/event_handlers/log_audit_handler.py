"""Subscribes to all domain events and logs them for audit purposes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import Logger
    from shell.domain.platform.events import DomainEvent


class LogAuditHandler:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def handle(self, event: DomainEvent) -> None:
        self._logger.info(
            "event",
            event_type=type(event).__name__,
            occurred_at=event.occurred_at.value.isoformat(),
        )
