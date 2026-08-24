"""ProcessedDeliveryStore — explicit delivery deduplication (fallback path).

The inbox processor commits the business change, the local outbox and the inbox
acknowledge in one transaction (session-scope, ref2.md §4.1), so SQL handlers
never need an extra dedup row. This store exists for handlers that cannot share
the processor's transaction (different DB / non-shared UoW): such a handler
writes a ``processed_delivery`` row atomically with its own change and the
processor consults it before dispatch, so a redelivery is a no-op.

Implements :class:`shell.platform.application.ports.transport.delivery_dedup_store.DeliveryDedupStore`:

- ``is_duplicate`` / ``mark_processed`` resolve their session from the active
  delivery session scope (safe inside a handler running under the processor);
- ``*_in_session`` variants take an explicit session (processor, adapters, tests).

A unique-key conflict on ``(consumer_name, outbox_id)`` in ``mark_processed``
means the delivery was already processed and is treated as success — the dedup
row is never written in a separate transaction before the business effect.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from shell.platform.infrastructure.context import get_session_scope

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Mapped

    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator


class _ProcessedDeliveryModel(Protocol):
    """Columns the dedup model must expose for the store."""

    id: Mapped[str]
    consumer_name: Mapped[str]
    outbox_id: Mapped[str]
    payload: Mapped[dict[str, object]]
    processed_at: Mapped[object]


class ProcessedDeliveryStore:
    def __init__(
        self,
        model: type[_ProcessedDeliveryModel],
        consumer_name: str,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        self._model = model
        self._consumer_name = consumer_name
        from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
            UuidTechnicalIdGenerator,
        )

        self._id_generator = id_generator or UuidTechnicalIdGenerator()

    # ------------------------------------------------------------------
    # DeliveryDedupStore (ambient scope)
    # ------------------------------------------------------------------

    async def is_duplicate(self, outbox_id: str) -> bool:
        session = self._require_scope_session()
        return await self.is_duplicate_in_session(session, outbox_id)

    async def mark_processed(
        self,
        outbox_id: str,
        *,
        payload: dict[str, object] | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        session = self._require_scope_session()
        await self.mark_processed_in_session(
            session, outbox_id, payload=payload, processed_at=processed_at
        )

    # ------------------------------------------------------------------
    # Explicit-session operations (processor, adapters, tests)
    # ------------------------------------------------------------------

    async def is_duplicate_in_session(self, session: AsyncSession, outbox_id: str) -> bool:
        result = await session.execute(
            select(self._model.id).where(
                self._model.consumer_name == self._consumer_name,
                self._model.outbox_id == outbox_id,
            )
        )
        return result.first() is not None

    async def mark_processed_in_session(
        self,
        session: AsyncSession,
        outbox_id: str,
        *,
        payload: dict[str, object] | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        try:
            # Keep the conflict inside a savepoint so the outer processing
            # transaction remains usable for the idempotent ack.
            async with session.begin_nested():
                await session.execute(
                    insert(self._model).values(
                        id=self._id_generator.new_id(),
                        consumer_name=self._consumer_name,
                        outbox_id=outbox_id,
                        payload=payload or {},
                        processed_at=processed_at or datetime.now(tz=UTC),
                    )
                )
        except IntegrityError:
            # A unique-key conflict on (consumer_name, outbox_id) means the
            # source record was already processed — idempotent no-op.
            return

    def _require_scope_session(self) -> AsyncSession:
        scope = get_session_scope()
        if scope is None:
            raise RuntimeError(
                "ProcessedDeliveryStore requires an active delivery session scope; "
                "use is_duplicate_in_session/mark_processed_in_session with an explicit "
                "session instead"
            )
        return cast("AsyncSession", scope.session)
