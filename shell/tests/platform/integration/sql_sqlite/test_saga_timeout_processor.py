"""SQLite integration tests for saga timeout scheduling and firing."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from shell.platform.infrastructure.persistence.memory import FakeEventPublisher
from shell.platform.infrastructure.process.saga.repositories.sql_saga_timeout_repository import (
    SqlSagaTimeoutRepository,
)
from shell.platform.infrastructure.process.saga.worker.saga_timeout_processor import (
    SagaTimeoutProcessor,
)
from shell.platform.process.saga.saga_timed_out import SagaTimedOut
from shell.tests.platform.integration.platform_delivery_models import SAGA_DELIVERY_MODELS

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class _FailingPublisher:
    async def publish(self, events: object) -> None:
        raise RuntimeError("delivery down")


async def _create_saga_tables(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        connection = await session.connection()
        await connection.run_sync(SAGA_DELIVERY_MODELS.instance.metadata.create_all)


def _repository(session_factory: async_sessionmaker) -> SqlSagaTimeoutRepository:
    return SqlSagaTimeoutRepository(session_factory, SAGA_DELIVERY_MODELS, source_service="session")


class TestSagaTimeoutProcessor:
    async def test_fires_due_timeout(self, session_factory: async_sessionmaker) -> None:
        await _create_saga_tables(session_factory)
        await _repository(session_factory).schedule(
            saga_id="saga-1",
            saga_key="order-1",
            step="charge_payment",
            due_in=timedelta(seconds=-1),
        )
        event_bus = FakeEventPublisher()
        processor = SagaTimeoutProcessor(
            session_factory,
            event_bus,
            models=SAGA_DELIVERY_MODELS,
            max_retries=2,
            retry_backoff_seconds=0,
        )

        result = await processor.run_once()

        assert result.claimed_count == 1
        assert result.processed_count == 1
        assert len(event_bus.published) == 1
        timed_out = event_bus.published[0]
        assert isinstance(timed_out, SagaTimedOut)
        assert timed_out.saga_id == "saga-1"
        assert timed_out.saga_key == "order-1"
        assert timed_out.step == "charge_payment"

    async def test_does_not_claim_future_timeout(self, session_factory: async_sessionmaker) -> None:
        await _create_saga_tables(session_factory)
        await _repository(session_factory).schedule(
            saga_id="saga-2",
            saga_key="order-2",
            step="charge_payment",
            due_in=timedelta(minutes=5),
        )
        event_bus = FakeEventPublisher()
        processor = SagaTimeoutProcessor(session_factory, event_bus, models=SAGA_DELIVERY_MODELS)

        result = await processor.run_once()

        assert result.claimed_count == 0
        assert event_bus.published == []

    async def test_publish_failure_retries_then_dlq(
        self, session_factory: async_sessionmaker
    ) -> None:
        await _create_saga_tables(session_factory)
        await _repository(session_factory).schedule(
            saga_id="saga-3",
            saga_key="order-3",
            step="release_stock",
            due_in=timedelta(seconds=-1),
        )
        processor = SagaTimeoutProcessor(
            session_factory,
            _FailingPublisher(),
            models=SAGA_DELIVERY_MODELS,
            max_retries=2,
            retry_backoff_seconds=0,
        )

        first = await processor.run_once()
        assert first.retried_count == 1
        second = await processor.run_once()
        assert second.dead_lettered_count == 1
