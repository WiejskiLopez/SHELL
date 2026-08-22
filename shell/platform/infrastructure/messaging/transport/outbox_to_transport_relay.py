"""OutboxToTransportRelay — reads pending outbox rows and publishes them via DeliveryTransport.

This is the producer-side bridge between the transactional outbox and the broker:
  - reads ``outbox_*`` rows with ``published_at IS NULL`` (FOR UPDATE SKIP LOCKED on PG);
  - builds a DeliveryEnvelope and calls ``transport.deliver(...)``;
  - marks ``published_at`` only after a successful delivery.

A record is never marked published before the broker acknowledged it, so a crash
between deliver and mark simply re-delivers (at-least-once; the consumer inbox is
idempotent).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped

    from shell.platform.application.ports.transport.delivery_transport import (
        DeliveryEnvelope,
        DeliveryKind,
        DeliveryTransport,
    )
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )
    from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
        EventDeliveryModels,
    )
    from shell.platform.infrastructure.persistence.sql.models.message_delivery import (
        MessageDeliveryModels,
    )

logger = logging.getLogger(__name__)


class DeliveryOutboxModel(Protocol):
    """Outbox columns shared by all delivery kinds, used for the pending-row SELECT."""

    id: Mapped[str]
    event_id: Mapped[str]
    source_service: Mapped[str]
    occurred_at: Mapped[datetime]
    aggregate_id: Mapped[str]
    aggregate_name: Mapped[str]
    schema_version: Mapped[int]
    payload: Mapped[dict[str, object]]
    correlation_id: Mapped[str]
    causation_id: Mapped[str]
    published_at: Mapped[datetime | None]


class DeliveryOutboxRow(Protocol):
    """Runtime instance shape of a pending outbox row."""

    id: str
    event_id: str
    source_service: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    published_at: datetime | None


class OutboxToTransportRelay:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: EventDeliveryModels | MessageDeliveryModels | CommandDeliveryModels,
        transport: DeliveryTransport,
        kind: DeliveryKind,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._outbox_model = cast("type[DeliveryOutboxModel]", models.outbox)
        self._transport = transport
        self._kind = kind
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(self._outbox_model)
                .where(self._outbox_model.published_at.is_(None))
                .order_by(self._outbox_model.occurred_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            now = datetime.now(tz=UTC)
            envelopes = [self._to_envelope(row) for row in rows]

            for envelope in envelopes:
                await self._transport.deliver(envelope)

            for row in rows:
                cast("DeliveryOutboxRow", row).published_at = now
            await session.commit()
            return len(rows)

    def _to_envelope(self, row: object) -> DeliveryEnvelope:
        from shell.platform.application.ports.transport.delivery_transport import DeliveryEnvelope

        typed_row = cast("DeliveryOutboxRow", row)
        contract_type = cast("str", getattr(typed_row, f"{self._kind}_type"))
        return DeliveryEnvelope(
            kind=self._kind,
            outbox_id=typed_row.id,
            contract_type=contract_type,
            occurred_at=typed_row.occurred_at,
            payload=typed_row.payload,
            correlation_id=typed_row.correlation_id,
            causation_id=typed_row.causation_id,
            event_id=getattr(typed_row, "event_id", None),
            source_service=getattr(typed_row, "source_service", None),
            aggregate_id=getattr(typed_row, "aggregate_id", None),
            aggregate_name=getattr(typed_row, "aggregate_name", None),
            schema_version=getattr(typed_row, "schema_version", 1),
        )
