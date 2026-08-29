"""InboxMetricsService — minimal backlog/health metrics for inbox delivery.

Provides the operational numbers needed for dashboards and readiness checks
without coupling the platform to a specific metrics backend (Prometheus etc.).
Consumers may convert the returned snapshot into counters of their choice.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import func, select

from shell.platform.domain.value_objects.inbox_status import InboxStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )
    from shell.platform.observability.application.ports.metrics import MetricsBackend

logger = logging.getLogger(__name__)


class _MetricRow(Protocol):
    """Read shape of the aggregate metric rows."""

    status: str
    count: int
    oldest_pending_at: object


@dataclass(frozen=True, slots=True)
class InboxMetrics:
    pending: int = 0
    processing: int = 0
    processed: int = 0
    retry: int = 0
    dead_letter: int = 0
    total: int = 0
    oldest_pending_age_seconds: float | None = None
    by_status: dict[str, int] = field(default_factory=dict)


class InboxMetricsService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        inbox_model: type[InboxStateModel],
        backend: MetricsBackend | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._inbox_model = inbox_model
        self._backend = backend

    async def snapshot(self) -> InboxMetrics:
        """Return a backlog snapshot of the inbox table."""
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(
                        self._inbox_model.status,
                        func.count().label("count"),
                    ).group_by(self._inbox_model.status)
                )
            ).all()

            oldest = (
                await session.execute(
                    select(func.min(self._inbox_model.received_at)).where(
                        self._inbox_model.status.in_(
                            [InboxStatus.PENDING.value, InboxStatus.RETRY.value]
                        )
                    )
                )
            ).scalar_one()

        by_status = {row[0]: int(row[1]) for row in rows}
        metrics = InboxMetrics(
            pending=by_status.get(InboxStatus.PENDING.value, 0),
            processing=by_status.get(InboxStatus.PROCESSING.value, 0),
            processed=by_status.get(InboxStatus.PROCESSED.value, 0),
            retry=by_status.get(InboxStatus.RETRY.value, 0),
            dead_letter=by_status.get(InboxStatus.DEAD_LETTER.value, 0),
            total=sum(by_status.values()),
            oldest_pending_age_seconds=self._age_seconds(oldest),
            by_status=by_status,
        )
        self._emit(metrics)
        return metrics

    def _emit(self, metrics: InboxMetrics) -> None:
        if self._backend is None:
            return
        try:
            self._backend.record_backlog(
                pending=metrics.pending,
                processing=metrics.processing,
                processed=metrics.processed,
                retry=metrics.retry,
                dead_letter=metrics.dead_letter,
                oldest_pending_age_seconds=metrics.oldest_pending_age_seconds,
            )
        except Exception:
            logger.exception("metrics backend failed to record backlog snapshot")

    @staticmethod
    def _age_seconds(oldest: object | None) -> float | None:
        if oldest is None:
            return None
        from datetime import UTC, datetime

        value = oldest
        if not isinstance(value, datetime):
            value = datetime.fromisoformat(str(value))
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        age = (datetime.now(tz=UTC) - value).total_seconds()
        return max(age, 0.0)
