from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import update

from shell.platform.infrastructure.context import (
    get_causation_id,
    get_or_create_correlation_id,
    get_session_scope,
)

if TYPE_CHECKING:
    from saga_orchestration.infrastructure.process.saga.models.saga_delivery import (
        SagaDeliveryModels,
    )


class SqlSagaTimeoutRepository:
    def __init__(
        self,
        session_factory: Any,
        models: SagaDeliveryModels,
        source_service: str,
        id_generator: Any | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._timeout_model = models.timeout
        self._source_service = source_service
        if id_generator is None:
            from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
                UuidTechnicalIdGenerator,
            )

            id_generator = UuidTechnicalIdGenerator()
        self._id_generator = id_generator

    def _new_id(self) -> str:
        generator = self._id_generator
        return str(generator.new_id() if hasattr(generator, "new_id") else generator())

    @asynccontextmanager
    async def _session(self) -> Any:
        scope = get_session_scope()
        if scope is not None and scope.session is not None:
            yield cast("Any", scope.session), False
            return
        async with self._session_factory() as session:
            yield session, True

    async def schedule(self, *, saga_id: str, saga_key: str, step: str, due_in: timedelta) -> None:
        now = datetime.now(tz=UTC)
        async with self._session() as (session, commit_owned):
            session.add(
                self._timeout_model(
                    id=self._new_id(),
                    outbox_id=self._new_id(),
                    saga_id=saga_id,
                    saga_key=saga_key,
                    step=step,
                    source_service=self._source_service,
                    due_at=now + due_in,
                    status="PENDING",
                    payload={},
                    correlation_id=get_or_create_correlation_id(),
                    causation_id=get_causation_id(),
                    received_at=now,
                    next_attempt_at=now + due_in,
                )
            )
            if commit_owned:
                await session.commit()

    async def cancel(self, *, saga_id: str, step: str) -> None:
        async with self._session() as (session, commit_owned):
            await session.execute(
                update(self._timeout_model)
                .where(
                    self._timeout_model.saga_id == saga_id,
                    self._timeout_model.step == step,
                    self._timeout_model.status.in_(("PENDING", "RETRY")),
                )
                .values(status="PROCESSED")
            )
            if commit_owned:
                await session.commit()
