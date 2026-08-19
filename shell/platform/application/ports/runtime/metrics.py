from __future__ import annotations

from typing import Protocol


class MetricsBackend(Protocol):
    def record_backlog(
        self,
        *,
        pending: int,
        processing: int,
        processed: int,
        retry: int,
        dead_letter: int,
        oldest_pending_age_seconds: float | None,
    ) -> None: ...

    def record_lease_expired(self, count: int) -> None: ...

    def record_duplicate_delivery(self, count: int) -> None: ...
