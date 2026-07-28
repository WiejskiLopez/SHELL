"""InboxProcessor — consumes Inbox events and triggers application logic via EventBus.

Guarantees at-least-once delivery:
  1. Publish event FIRST (within DB transaction)
  2. Mark processed_at only on success
  3. On failure: increment retry_count, apply backoff, eventually DLQ
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

from sqlalchemy import and_, or_, select

from shell.platform.infrastructure.context import (
    causation_id_var,
    correlation_id_var,
)
from shell.platform.infrastructure.persistence.sql.models import InboxEventModel
from shell.platform.infrastructure.serialization.event_deserializer import EventDeserializer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.ports import EventPublisher
    from shell.platform.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class InboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventPublisher,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_backoff_seconds: int = 30,
        registry: dict[str, type] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._deserializer = EventDeserializer(registry=registry)

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            backoff_cutoff = datetime.now(tz=UTC) - timedelta(seconds=self._retry_backoff_seconds)

            stmt = (
                select(InboxEventModel)
                .where(
                    and_(
                        InboxEventModel.retry_count < self._max_retries,
                        InboxEventModel.processed_at.is_(None),
                        or_(
                            InboxEventModel.last_attempted_at.is_(None),
                            InboxEventModel.last_attempted_at < backoff_cutoff,
                        ),
                    )
                )
                .order_by(InboxEventModel.received_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            now = datetime.now(tz=UTC)
            processed_count = 0

            for row in rows:
                domain_event = self._deserializer.deserialize(
                    row.event_type, row.occurred_at, row.payload
                )

                if domain_event is None:
                    row.retry_count += 1
                    row.last_attempted_at = now
                    row.error = f"Deserialization failed for type: {row.event_type}"
                    if row.retry_count >= self._max_retries:
                        row.processed_at = now
                        logger.critical(
                            "Event %s (%s) exceeded max_retries=%s after deserialization failure — DLQ",
                            row.id,
                            row.event_type,
                            self._max_retries,
                        )
                    continue

                domain_event = cast("DomainEvent", domain_event)
                corr_token = correlation_id_var.set(row.correlation_id)
                caus_token = causation_id_var.set(domain_event.event_id.value)
                try:
                    await self._event_bus.publish([domain_event])

                    row.processed_at = now
                    row.retry_count = 0
                    row.last_attempted_at = None
                    row.error = None
                    processed_count += 1
                except Exception as exc:
                    row.retry_count += 1
                    row.last_attempted_at = now
                    row.error = f"{type(exc).__name__}: {exc}"
                    if row.retry_count >= self._max_retries:
                        row.processed_at = now
                        logger.critical(
                            "Event %s (%s) exceeded max_retries=%s — DLQ",
                            row.id,
                            row.event_type,
                            self._max_retries,
                        )
                finally:
                    correlation_id_var.reset(corr_token)
                    causation_id_var.reset(caus_token)

            await session.commit()
            return processed_count
