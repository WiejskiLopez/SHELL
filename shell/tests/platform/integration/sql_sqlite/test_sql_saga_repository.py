"""SQLite integration tests for SqlSagaRepository operations and locking."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from saga_orchestration.infrastructure.process.saga.repositories.sql_saga_repository import (
    SqlSagaRepository,
)
from saga_orchestration.process.saga.base.saga_state import SagaStatus
from saga_orchestration.process.saga.errors import ConcurrentModificationError
from saga_orchestration.process.saga.saga_instance import SagaInstance

from shell.tests.platform.integration.platform_delivery_models import SAGA_DELIVERY_MODELS

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


async def _create_saga_tables(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        connection = await session.connection()
        await connection.run_sync(SAGA_DELIVERY_MODELS.instance.metadata.create_all)


class TestSqlSagaRepository:
    async def test_save_and_get_by_key(self, session_factory: async_sessionmaker) -> None:
        await _create_saga_tables(session_factory)
        repository = SqlSagaRepository(session_factory, SAGA_DELIVERY_MODELS)
        instance = SagaInstance(
            saga_id="saga-1",
            saga_type="order_fulfillment",
            saga_key="order-1",
            status=SagaStatus.RUNNING,
            business_payload={"order_id": "order-1"},
        )
        await repository.create(instance)

        loaded = await repository.get_by_key("order_fulfillment", "order-1")
        assert loaded is not None
        assert loaded.saga_id == "saga-1"
        assert loaded.saga_key == "order-1"
        assert loaded.status is SagaStatus.RUNNING
        assert loaded.business_payload == {"order_id": "order-1"}
        assert loaded.version == 1

    async def test_missing_key_returns_none(self, session_factory: async_sessionmaker) -> None:
        await _create_saga_tables(session_factory)
        repository = SqlSagaRepository(session_factory, SAGA_DELIVERY_MODELS)
        assert await repository.get_by_key("order_fulfillment", "missing") is None

    async def test_update_increments_version(self, session_factory: async_sessionmaker) -> None:
        await _create_saga_tables(session_factory)
        repository = SqlSagaRepository(session_factory, SAGA_DELIVERY_MODELS)
        instance = SagaInstance(
            saga_id="saga-2",
            saga_type="order_fulfillment",
            saga_key="order-2",
            status=SagaStatus.RUNNING,
        )
        await repository.create(instance)

        first = await repository.get_by_key("order_fulfillment", "order-2")
        assert first is not None
        updated = SagaInstance(
            saga_id=first.saga_id,
            saga_type=first.saga_type,
            saga_key=first.saga_key,
            status=SagaStatus.COMPLETED,
            completed_steps=("charge_payment",),
            current_step=None,
            business_payload=first.business_payload,
            version=first.version,
        )
        await repository.update(updated)

        loaded = await repository.get_by_key("order_fulfillment", "order-2")
        assert loaded is not None
        assert loaded.status is SagaStatus.COMPLETED
        assert loaded.completed_steps == ("charge_payment",)
        assert loaded.version == 2

    async def test_stale_version_raises_concurrency_error(
        self, session_factory: async_sessionmaker
    ) -> None:
        await _create_saga_tables(session_factory)
        repository = SqlSagaRepository(session_factory, SAGA_DELIVERY_MODELS)
        instance = SagaInstance(
            saga_id="saga-3",
            saga_type="order_fulfillment",
            saga_key="order-3",
            status=SagaStatus.RUNNING,
        )
        await repository.create(instance)

        first = await repository.get_by_key("order_fulfillment", "order-3")
        assert first is not None
        update_one = SagaInstance(
            saga_id=first.saga_id,
            saga_type=first.saga_type,
            saga_key=first.saga_key,
            status=SagaStatus.COMPLETED,
            business_payload=first.business_payload,
            version=first.version,
        )
        await repository.update(update_one)

        stale = SagaInstance(
            saga_id=first.saga_id,
            saga_type=first.saga_type,
            saga_key=first.saga_key,
            status=SagaStatus.FAILING,
            business_payload=first.business_payload,
            version=first.version,
        )
        with pytest.raises(ConcurrentModificationError):
            await repository.update(stale)
