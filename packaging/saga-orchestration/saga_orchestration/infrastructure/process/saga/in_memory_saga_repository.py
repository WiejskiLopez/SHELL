from __future__ import annotations

from saga_orchestration.process.saga.errors import ConcurrentModificationError
from saga_orchestration.process.saga.saga_instance import SagaInstance


class InMemorySagaRepository:
    """Deterministic repository adapter for tests and local execution."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], SagaInstance] = {}

    async def get_by_key(self, saga_type: str, saga_key: str) -> SagaInstance | None:
        return self._store.get((saga_type, saga_key))

    async def create(self, instance: SagaInstance) -> None:
        key = (instance.saga_type, instance.saga_key)
        if key in self._store:
            raise ValueError(f"Saga already exists: {instance.saga_type}:{instance.saga_key}")
        self._store[key] = instance

    async def update(self, instance: SagaInstance) -> None:
        key = (instance.saga_type, instance.saga_key)
        existing = self._store.get(key)
        if existing is None:
            raise KeyError(f"Saga does not exist: {instance.saga_type}:{instance.saga_key}")
        if existing.version != instance.version:
            raise ConcurrentModificationError("Saga", instance.saga_id)
        self._store[key] = SagaInstance(
            saga_id=instance.saga_id,
            saga_type=instance.saga_type,
            saga_key=instance.saga_key,
            status=instance.status,
            business_payload=dict(instance.business_payload),
            completed_steps=tuple(instance.completed_steps),
            failed_steps=tuple(instance.failed_steps),
            current_step=instance.current_step,
            version=instance.version + 1,
            created_at=existing.created_at,
            updated_at=instance.updated_at,
            completed_at=instance.completed_at,
            failed_at=instance.failed_at,
            compensated_at=instance.compensated_at,
        )
