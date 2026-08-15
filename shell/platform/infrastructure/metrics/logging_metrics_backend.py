"""LoggingMetricsBackend — dependency-free MetricsBackend adapter.

Implements :class:`shell.platform.application.ports.metrics.MetricsBackend` by
logging every snapshot. Used until a real backend (Prometheus, etc.) is wired;
keeps the platform free of a concrete metrics dependency (ref4.md Krok 4).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LoggingMetricsBackend:
    """Pushes backlog/lease/duplicate metrics to the application log."""

    def record_backlog(
        self,
        *,
        pending: int,
        processing: int,
        processed: int,
        retry: int,
        dead_letter: int,
        legacy_review: int,
        oldest_pending_age_seconds: float | None,
    ) -> None:
        logger.info(
            "inbox.backlog pending=%s processing=%s processed=%s retry=%s dead_letter=%s "
            "legacy_review=%s oldest_pending_age_seconds=%s",
            pending,
            processing,
            processed,
            retry,
            dead_letter,
            legacy_review,
            oldest_pending_age_seconds,
        )

    def record_lease_expired(self, count: int) -> None:
        logger.warning("inbox.lease_expired count=%s", count)

    def record_duplicate_delivery(self, count: int) -> None:
        logger.warning("inbox.duplicate_delivery count=%s", count)
