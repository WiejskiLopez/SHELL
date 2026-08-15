"""MetricsBackend — pluggable sink for inbox delivery metrics.

The platform never depends on a concrete metrics backend (Prometheus etc.).
``InboxMetricsService`` pushes snapshots to any registered ``MetricsBackend``;
adapters live in infrastructure and convert the primitives into counters/gauges
of their choice.
"""

from __future__ import annotations

from typing import Protocol


class MetricsBackend(Protocol):
    """Receives a backlog snapshot produced by ``InboxMetricsService``."""

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
    ) -> None: ...

    def record_lease_expired(self, count: int) -> None: ...

    def record_duplicate_delivery(self, count: int) -> None: ...
