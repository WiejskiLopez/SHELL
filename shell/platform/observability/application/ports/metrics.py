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

    def record_outbox_backlog(self, *, pending: int) -> None: ...

    def record_lease_expired(self, count: int) -> None: ...

    def record_duplicate_delivery(self, count: int) -> None: ...


class MetricsExporter(Protocol):
    def render(self) -> str: ...


class InboundHttpMetricsRecorder(Protocol):
    def record_inbound_request(
        self,
        *,
        service: str,
        method: str,
        status: int,
        duration_seconds: float,
    ) -> None: ...


class OutboundHttpMetricsRecorder(Protocol):
    def record_outbound_attempt(self, *, target_service: str, method: str) -> None: ...

    def record_outbound_retry(self, *, target_service: str, method: str) -> None: ...

    def record_circuit_trip(self, *, target_service: str, method: str) -> None: ...

    def record_circuit_reject(self, *, target_service: str, method: str) -> None: ...

    def record_circuit_state(self, *, target_service: str, method: str, state: str) -> None: ...
