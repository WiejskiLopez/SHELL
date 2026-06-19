"""Long-running background worker for Outbox Relay + Inbox Processor."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.infrastructure.platform.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
    from shell.infrastructure.platform.messaging.processor.inbox_processor import InboxProcessor

logger = logging.getLogger(__name__)


class MessagingWorker:
    """
    Runs OutboxRelay and InboxProcessor in a continuous loop with exponential backoff.

    Designed for production deployment as a separate process/container.
    Exposes health status via is_healthy() for monitoring probes.
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
        self._healthy = True
        self._iteration_count = 0
        self._last_successful_iteration: float = 0.0
        self._last_error: str | None = None

    async def run(self) -> None:
        """Run the worker loop until stopped."""
        self._running = True
        while self._running:
            try:
                outbox_count = await asyncio.wait_for(
                    self._outbox_to_inbox_relay.run_once(), timeout=30.0
                )
                inbox_count = await asyncio.wait_for(
                    self._inbox_processor.run_once(), timeout=30.0
                )

                self._iteration_count += 1
                self._last_successful_iteration = asyncio.get_event_loop().time()
                self._healthy = True
                self._last_error = None

                total = outbox_count + inbox_count
                if total > 0:
                    self._current_backoff = self._poll_interval
                else:
                    await asyncio.sleep(self._current_backoff)
                    self._current_backoff = min(
                        self._current_backoff * self._backoff_factor, self._max_backoff
                    )

            except TimeoutError:
                logger.warning("Worker iteration timed out after 30s, backing off...")
                self._healthy = False
                self._last_error = "timeout"
                await asyncio.sleep(self._current_backoff)
                self._current_backoff = min(
                    self._current_backoff * self._backoff_factor, self._max_backoff
                )

            except asyncio.CancelledError:
                logger.info("Worker cancelled, shutting down gracefully.")
                self._running = False
                raise

            except (ConnectionError, OSError) as e:
                logger.error("Database connection error: %s, backing off...", e)
                self._healthy = False
                self._last_error = str(e)
                await asyncio.sleep(self._current_backoff)
                self._current_backoff = min(
                    self._current_backoff * self._backoff_factor, self._max_backoff
                )

            except Exception:
                logger.exception("Unexpected error in worker loop, backing off...")
                self._healthy = False
                self._last_error = "unexpected"
                await asyncio.sleep(self._current_backoff)
                self._current_backoff = min(
                    self._current_backoff * self._backoff_factor, self._max_backoff
                )

    def stop(self) -> None:
        """Signal the worker to stop gracefully."""
        self._running = False

    def is_healthy(self) -> bool:
        """Return whether the worker considers itself healthy."""
        return self._healthy

    @property
    def health_status(self) -> dict:
        return {
            "healthy": self._healthy,
            "running": self._running,
            "iteration_count": self._iteration_count,
            "last_error": self._last_error,
            "current_backoff": self._current_backoff,
        }
