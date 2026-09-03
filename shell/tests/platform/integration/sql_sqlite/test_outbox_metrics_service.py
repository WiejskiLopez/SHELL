"""SQLite integration tests for OutboxMetricsService pending backlog."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import create_async_engine

from shell.platform.infrastructure.messaging.outbox.outbox_metrics_service import (
    OutboxMetricsService,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.observability.infrastructure.metrics.prometheus_metrics_backend import (
    PrometheusMetricsBackend,
)
from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry
from shell.tests.platform.integration.platform_delivery_models import (
    EVENT_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_OUTBOX_MODEL = EVENT_DELIVERY_MODELS.outbox
_EVENT_TYPE = "SampleIntegrationEvent"


async def _isolated_factory(tmp_path) -> async_sessionmaker:
    url = f"sqlite+aiosqlite:///{tmp_path / 'outbox-metrics.db'}"
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(_OUTBOX_MODEL.metadata.create_all)
    await engine.dispose()
    return build_session_factory(url)


async def _seed_outboxes(session_factory: async_sessionmaker, pending: int, published: int) -> None:
    async with session_factory() as session:
        for index in range(pending + published):
            session.add(
                _OUTBOX_MODEL(
                    id=f"outbox-metrics-{index}",
                    event_id=f"event-{index}",
                    integration_event_name=_EVENT_TYPE,
                    source_service="execution_service",
                    occurred_at=datetime.now(tz=UTC),
                    aggregate_id=f"aggregate-{index}",
                    schema_version=1,
                    payload={},
                    correlation_id="c",
                    causation_id="k",
                    published_at=None if index < pending else datetime.now(tz=UTC),
                )
            )
        await session.commit()


class TestOutboxMetricsService:
    async def test_snapshot_counts_pending_outbox_rows(self, tmp_path) -> None:
        session_factory = await _isolated_factory(tmp_path)
        await _seed_outboxes(session_factory, pending=3, published=2)
        service = OutboxMetricsService(session_factory, _OUTBOX_MODEL)

        pending = await service.snapshot()

        assert pending == 3

    async def test_snapshot_pushes_pending_into_prometheus_backend(self, tmp_path) -> None:
        session_factory = await _isolated_factory(tmp_path)
        await _seed_outboxes(session_factory, pending=4, published=1)
        registry = MetricsRegistry()
        backend = PrometheusMetricsBackend(registry)
        service = OutboxMetricsService(session_factory, _OUTBOX_MODEL, backend=backend)

        await service.snapshot()

        assert "outbox_backlog_pending 4.0" in registry.render()
