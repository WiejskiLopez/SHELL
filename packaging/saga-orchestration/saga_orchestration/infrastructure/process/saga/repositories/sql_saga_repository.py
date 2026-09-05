from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update

from saga_orchestration.process.saga.base.saga_state import SagaStatus
from saga_orchestration.process.saga.errors import ConcurrentModificationError
from saga_orchestration.process.saga.saga_instance import SagaInstance
from shell.platform.infrastructure.context import get_session_scope

if TYPE_CHECKING:
    from saga_orchestration.infrastructure.process.saga.models.saga_delivery import (
        SagaDeliveryModels,
    )


class SqlSagaRepository:
    def __init__(self, session_factory: Any, models: SagaDeliveryModels) -> None:
        self._session_factory = session_factory
        self._instance_model = models.instance

    @asynccontextmanager
    async def _session(self) -> Any:
        scope = get_session_scope()
        if scope is not None and scope.session is not None:
            yield scope.session, False
            return
        async with self._session_factory() as session:
            yield session, True

    async def get_by_key(self, saga_type: str, saga_key: str) -> SagaInstance | None:
        async with self._session() as (session, _):
            row = (
                await session.execute(
                    select(self._instance_model).where(
                        self._instance_model.saga_type == saga_type,
                        self._instance_model.saga_key == saga_key,
                    )
                )
            ).scalar_one_or_none()
            return None if row is None else self._to_instance(row)

    async def create(self, instance: SagaInstance) -> None:
        now = datetime.now(tz=UTC)
        async with self._session() as (session, commit_owned):
            session.add(
                self._instance_model(
                    id=instance.saga_id,
                    saga_type=instance.saga_type,
                    saga_key=instance.saga_key,
                    status=instance.status.value,
                    current_step=instance.current_step,
                    business_payload=dict(instance.business_payload),
                    completed_steps=list(instance.completed_steps),
                    failed_steps=list(instance.failed_steps),
                    version=instance.version,
                    created_at=instance.created_at or now,
                    updated_at=instance.updated_at or now,
                    completed_at=instance.completed_at,
                    failed_at=instance.failed_at,
                    compensated_at=instance.compensated_at,
                )
            )
            if commit_owned:
                await session.commit()

    async def update(self, instance: SagaInstance) -> None:
        async with self._session() as (session, commit_owned):
            result = await session.execute(
                update(self._instance_model)
                .where(
                    self._instance_model.id == instance.saga_id,
                    self._instance_model.version == instance.version,
                )
                .values(
                    status=instance.status.value,
                    current_step=instance.current_step,
                    business_payload=dict(instance.business_payload),
                    completed_steps=list(instance.completed_steps),
                    failed_steps=list(instance.failed_steps),
                    version=instance.version + 1,
                    updated_at=instance.updated_at or datetime.now(tz=UTC),
                    completed_at=instance.completed_at,
                    failed_at=instance.failed_at,
                    compensated_at=instance.compensated_at,
                )
            )
            if result.rowcount != 1:
                if commit_owned:
                    await session.rollback()
                raise ConcurrentModificationError("Saga", instance.saga_id)
            if commit_owned:
                await session.commit()

    def _to_instance(self, row: Any) -> SagaInstance:
        return SagaInstance(
            saga_id=row.id,
            saga_type=row.saga_type,
            saga_key=row.saga_key,
            status=SagaStatus(row.status),
            business_payload=dict(row.business_payload or {}),
            completed_steps=tuple(row.completed_steps or ()),
            failed_steps=tuple(row.failed_steps or ()),
            current_step=row.current_step,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
            completed_at=row.completed_at,
            failed_at=row.failed_at,
            compensated_at=row.compensated_at,
        )
