"""Unit tests for InMemorySagaRepository (deterministic fake)."""

from __future__ import annotations

import pytest
from saga_orchestration.infrastructure.process.saga.in_memory_saga_repository import (
    InMemorySagaRepository,
)
from saga_orchestration.process.saga.base.saga_state import SagaStatus
from saga_orchestration.process.saga.errors import ConcurrentModificationError
from saga_orchestration.process.saga.saga_instance import SagaInstance


class TestInMemorySagaRepository:
    async def test_save_and_get_by_key(self) -> None:
        repository = InMemorySagaRepository()
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

    async def test_update_increments_version(self) -> None:
        repository = InMemorySagaRepository()
        instance = SagaInstance(
            saga_id="saga-2",
            saga_type="order_fulfillment",
            saga_key="order-2",
            status=SagaStatus.RUNNING,
        )
        await repository.create(instance)
        first = await repository.get_by_key("order_fulfillment", "order-2")
        assert first is not None

        await repository.update(
            SagaInstance(
                saga_id=first.saga_id,
                saga_type=first.saga_type,
                saga_key=first.saga_key,
                status=SagaStatus.COMPLETED,
                version=first.version,
            )
        )
        loaded = await repository.get_by_key("order_fulfillment", "order-2")
        assert loaded is not None
        assert loaded.status is SagaStatus.COMPLETED
        assert loaded.version == 2

    async def test_stale_version_raises(self) -> None:
        repository = InMemorySagaRepository()
        instance = SagaInstance(
            saga_id="saga-3",
            saga_type="order_fulfillment",
            saga_key="order-3",
            status=SagaStatus.RUNNING,
        )
        await repository.create(instance)
        first = await repository.get_by_key("order_fulfillment", "order-3")
        assert first is not None

        await repository.update(
            SagaInstance(
                saga_id=first.saga_id,
                saga_type=first.saga_type,
                saga_key=first.saga_key,
                status=SagaStatus.FAILING,
                version=first.version,
            )
        )
        stale = SagaInstance(
            saga_id=first.saga_id,
            saga_type=first.saga_type,
            saga_key=first.saga_key,
            status=SagaStatus.RUNNING,
            version=first.version,
        )
        with pytest.raises(ConcurrentModificationError):
            await repository.update(stale)
