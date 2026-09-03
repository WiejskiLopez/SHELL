"""SqlSagaTimeoutRepository — adapter SQL portu SagaTimeoutRepository.

Timeouty zapisywane są jako rekordy ``saga_timeout`` z ``InboxStateMixin``
(next_attempt_at = due_at), więc odpalanie przechodzi przez istniejący
``InboxClaimService`` / ``InboxProcessorBase`` (lease, retry, DLQ za darmo).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import update

from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.infrastructure.context import (
    get_causation_id,
    get_or_create_correlation_id,
    get_session_scope,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.infrastructure.process.saga.models.saga_delivery import (
        SagaDeliveryModels,
    )


class SqlSagaTimeoutRepository:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: SagaDeliveryModels,
        source_service: str,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._source_service = source_service
        self._timeout_model: Any = models.timeout
        if id_generator is None:
            from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
                UuidTechnicalIdGenerator,
            )

            id_generator = UuidTechnicalIdGenerator()
        self._id_generator = id_generator

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[tuple[AsyncSession, bool]]:
        scope = get_session_scope()
        if scope is not None and scope.session is not None:
            yield cast("AsyncSession", scope.session), False
            return
        async with self._session_factory() as session:
            yield session, True

    async def schedule(
        self,
        *,
        saga_id: str,
        saga_key: str,
        step: str,
        due_in: timedelta,
    ) -> None:
        """Zapisuje timeout jako rekord gotowy do claimu po ``due_at``."""
        now = datetime.now(tz=UTC)
        due_at = now + due_in
        async with self._session() as (session, commit_owned):
            session.add(
                self._timeout_model(
                    id=str(self._id_generator.new_id()),
                    outbox_id=str(self._id_generator.new_id()),
                    saga_id=saga_id,
                    saga_key=saga_key,
                    step=step,
                    source_service=self._source_service,
                    due_at=due_at,
                    payload={},
                    correlation_id=get_or_create_correlation_id(),
                    causation_id=get_causation_id(),
                    received_at=now,
                    next_attempt_at=due_at,
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
                    self._timeout_model.status.in_(
                        (InboxStatus.PENDING.value, InboxStatus.RETRY.value)
                    ),
                )
                .values(
                    status=InboxStatus.PROCESSED.value,
                    processed_at=datetime.now(tz=UTC),
                    lease_until=None,
                    claimed_by=None,
                )
            )
            if commit_owned:
                await session.commit()
