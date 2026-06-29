"""Subscribes to all domain events and logs them for audit purposes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import Logger
    from shell.domain.platform.events import DomainEvent


class LogAuditHandler:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def handle(self, domain_event: DomainEvent) -> None:
        self._logger.info(
            "domain_event",
            event_type=type(domain_event).__name__,
            occurred_at=domain_event.occurred_at.value.isoformat(),
        )
