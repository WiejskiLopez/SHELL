"""Long-running background worker for Outbox Relay + Inbox Processor."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell.infrastructure.messaging.processor.inbox_processor import InboxProcessor

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from shell.application.ports.ports import EventPublisher
    from shell.infrastructure.messaging.outbox_to_inbox_relay import OutboxToInboxRelay


class MessagingWorker:
    """
    Runs OutboxRelay and InboxProcessor in a continuous loop with exponential backoff.

    Designed for production deployment as a separate process/container.
    """

    def __init__(
            self,
            outbox_to_inbox_relay: OutboxToInboxRelay,
            inbox_processor: InboxProcessor,
            poll_interval: float = 1.0,
            backoff_factor: float = 2.0,
            max_backoff: float = 30.0,
    ) -> None:
        self._outbox_to_inbox_relay = outbox_to_inbox_relay
        self._inbox_processor = inbox_processor
        self._poll_interval = poll_interval
        self._backoff_factor = backoff_factor
        self._max_backoff = max_backoff
        self._current_backoff = poll_interval
        self._running = False

    async def run(self) -> None:
        """Run the worker loop until stopped."""
        self._running = True
        while self._running:
            try:
                # Run both in sequence (outbox first, then inbox)
                outbox_count = await self._outbox_to_inbox_relay.run_once()
                inbox_count = await self._inbox_processor.run_once()

                total = outbox_count + inbox_count
                if total > 0:
                    # Reset backoff on activity
                    self._current_backoff = self._poll_interval
                else:
                    # Exponential backoff when idle
                    await asyncio.sleep(self._current_backoff)
                    self._current_backoff = min(
                        self._current_backoff * self._backoff_factor,
                        self._max_backoff
                    )
            except Exception:
                # Log error, apply backoff, continue
                await asyncio.sleep(self._current_backoff)
                self._current_backoff = min(
                    self._current_backoff * self._backoff_factor,
                    self._max_backoff
                )

    def stop(self) -> None:
        """Signal the worker to stop gracefully."""
        self._running = False