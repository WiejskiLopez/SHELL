"""ProcessedDeliveryStore — explicit delivery deduplication (fallback path).

The inbox processor commits the business change, the local outbox and the inbox
acknowledge in one transaction (session-scope, ref2.md §4.1), so SQL handlers
never need an extra dedup row. This store exists for handlers that cannot share
the processor's transaction (different DB / non-shared UoW): such a handler
writes a ``processed_delivery`` row atomically with its own change and the
processor consults it before dispatch, so a redelivery is a no-op.

Implements :class:`shell.platform.application.ports.delivery_dedup_store.DeliveryDedupStore`:

- ``is_duplicate`` / ``mark_processed`` resolve their session from the active
  delivery session scope (safe inside a handler running under the processor);
- ``*_in_session`` variants take an explicit session (processor, adapters, tests).

A unique-key conflict on ``(consumer_name, delivery_id)`` in ``mark_processed``
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


class _ProcessedDeliveryModel(Protocol):
    """Columns the dedup model must expose for the store."""

    id: Mapped[str]
    consumer_name: Mapped[str]
    delivery_id: Mapped[str]
    payload: Mapped[dict[str, object]]
    processed_at: Mapped[object]


class ProcessedDeliveryStore:
    def __init__(
        self,
        model: type[_ProcessedDeliveryModel],
        consumer_name: str,
    ) -> None:
        self._model = model
        self._consumer_name = consumer_name

    # ------------------------------------------------------------------
    # DeliveryDedupStore (ambient scope)
    # ------------------------------------------------------------------

    async def is_duplicate(self, delivery_id: str) -> bool:
        session = self._require_scope_session()
        return await self.is_duplicate_in_session(session, delivery_id)

    async def mark_processed(
        self,
        delivery_id: str,
        *,
        payload: dict[str, object] | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        session = self._require_scope_session()
        await self.mark_processed_in_session(
            session, delivery_id, payload=payload, processed_at=processed_at
        )

    # ------------------------------------------------------------------
    # Explicit-session operations (processor, adapters, tests)
    # ------------------------------------------------------------------

    async def is_duplicate_in_session(self, session: AsyncSession, delivery_id: str) -> bool:
        result = await session.execute(
            select(self._model.id).where(
                self._model.consumer_name == self._consumer_name,
                self._model.delivery_id == delivery_id,
            )
        )
        return result.first() is not None

    async def mark_processed_in_session(
        self,
        session: AsyncSession,
        delivery_id: str,
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
                        id=_new_id(),
                        consumer_name=self._consumer_name,
                        delivery_id=delivery_id,
                        payload=payload or {},
                        processed_at=processed_at or datetime.now(tz=UTC),
                    )
                )
        except IntegrityError:
            # A unique-key conflict on (consumer_name, delivery_id) means the
            # delivery was already processed — idempotent no-op.
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


def _new_id() -> str:
    import uuid

    return str(uuid.uuid4())
