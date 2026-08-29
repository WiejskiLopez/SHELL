"""PrometheusMetricsBackend — real MetricsBackend adapter over a MetricsRegistry.

Implements :class:`shell.platform.observability.application.ports.metrics.MetricsBackend`
by pushing delivery snapshots into Prometheus gauges/counters. It is wired in
place of ``LoggingMetricsBackend`` so every service exposes operational backlog
and delivery metrics on its ``/metrics`` endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry


class PrometheusMetricsBackend:
    """Pushes inbox/outbox/lease/duplicate metrics into a MetricsRegistry."""

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry
        self._backlog_pending = registry.gauge(
            "inbox_backlog_pending", help="Inbox records in PENDING state."
        )
        self._backlog_processing = registry.gauge(
            "inbox_backlog_processing", help="Inbox records in PROCESSING state."
        )
        self._backlog_processed = registry.gauge(
            "inbox_backlog_processed", help="Inbox records in PROCESSED state."
        )
        self._backlog_retry = registry.gauge(
            "inbox_backlog_retry", help="Inbox records in RETRY state."
        )
        self._backlog_dead_letter = registry.gauge(
            "inbox_backlog_dead_letter", help="Inbox records in DEAD_LETTER state."
        )
        self._oldest_pending_age = registry.gauge(
            "inbox_oldest_pending_age_seconds",
            help="Age of the oldest PENDING/RETRY inbox record in seconds.",
        )
        self._outbox_backlog_pending = registry.gauge(
            "outbox_backlog_pending",
            help="Outbox records awaiting publication (published_at is NULL).",
        )
        self._lease_expired = registry.counter(
            "inbox_lease_expired_total", help="Number of expired worker leases."
        )
        self._duplicate_delivery = registry.counter(
            "inbox_duplicate_delivery_total",
            help="Number of idempotently skipped duplicate deliveries.",
        )

    def record_backlog(
        self,
        *,
        pending: int,
        processing: int,
        processed: int,
        retry: int,
        dead_letter: int,
        oldest_pending_age_seconds: float | None,
    ) -> None:
        self._backlog_pending.set(float(pending))
        self._backlog_processing.set(float(processing))
        self._backlog_processed.set(float(processed))
        self._backlog_retry.set(float(retry))
        self._backlog_dead_letter.set(float(dead_letter))
        if oldest_pending_age_seconds is None:
            self._oldest_pending_age.set(-1.0)
        else:
            self._oldest_pending_age.set(float(oldest_pending_age_seconds))

    def record_outbox_backlog(self, *, pending: int) -> None:
        self._outbox_backlog_pending.set(float(pending))

    def record_lease_expired(self, count: int) -> None:
        self._lease_expired.inc(float(count))

    def record_duplicate_delivery(self, count: int) -> None:
        self._duplicate_delivery.inc(float(count))
