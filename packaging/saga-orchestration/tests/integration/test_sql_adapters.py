from __future__ import annotations

from datetime import timedelta

import pytest
from saga_orchestration.infrastructure.process.saga.models import build_saga_delivery_models
from saga_orchestration.infrastructure.process.saga.repositories.sql_saga_repository import (
    SqlSagaRepository,
)
from saga_orchestration.infrastructure.process.saga.repositories.sql_saga_timeout_repository import (
    SqlSagaTimeoutRepository,
)
from saga_orchestration.process.saga import SagaInstance, SagaStatus
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


@pytest.mark.asyncio
async def test_sql_saga_repository_round_trip() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    models = build_saga_delivery_models(Base)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlSagaRepository(sessions, models)
    instance = SagaInstance(
        saga_id="saga-1",
        saga_type="order_fulfillment",
        saga_key="order-1",
        status=SagaStatus.RUNNING,
    )

    await repository.create(instance)
    loaded = await repository.get_by_key("order_fulfillment", "order-1")
    assert loaded is not None
    assert loaded.saga_id == instance.saga_id
    assert loaded.saga_type == instance.saga_type
    assert loaded.saga_key == instance.saga_key
    assert loaded.status is SagaStatus.RUNNING

    await repository.update(
        SagaInstance(
            saga_id=instance.saga_id,
            saga_type=instance.saga_type,
            saga_key=instance.saga_key,
            status=SagaStatus.COMPLETED,
            version=instance.version,
        )
    )
    updated = await repository.get_by_key("order_fulfillment", "order-1")
    assert updated is not None
    assert updated.status is SagaStatus.COMPLETED
    assert updated.version == 2
    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_timeout_repository_schedules_and_cancels() -> None:
    class TimeoutBase(DeclarativeBase):
        pass

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    models = build_saga_delivery_models(TimeoutBase)
    async with engine.begin() as connection:
        await connection.run_sync(TimeoutBase.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    sequence = iter(("timeout-1", "outbox-1"))
    repository = SqlSagaTimeoutRepository(
        sessions,
        models,
        source_service="test",
        id_generator=lambda: next(sequence),
    )

    await repository.schedule(
        saga_id="saga-1",
        saga_key="order-1",
        step="charge",
        due_in=timedelta(seconds=5),
    )
    await repository.cancel(saga_id="saga-1", step="charge")

    async with sessions() as session:
        row = await session.get(models.timeout, "timeout-1")
        assert row is not None
        assert row.status == "PROCESSED"
    await engine.dispose()
