"""EventOutboxRelay — reads pending ``outbox_event`` rows and publishes via the event transport."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import select

from shell.platform.application.ports.transport.event_transport import (
    IntegrationEventDeliveryEnvelope,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped

    from shell.platform.application.ports.transport.event_transport import (
        IntegrationEventDeliveryTransport,
    )
    from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
        EventDeliveryModels,
    )


class EventOutboxModel(Protocol):
    id: Mapped[str]
    integration_event_name: Mapped[str]
    occurred_at: Mapped[datetime]
    source_service: Mapped[str]
    event_id: Mapped[str]
    aggregate_id: Mapped[str]
    schema_version: Mapped[int]
    payload: Mapped[dict[str, object]]
    correlation_id: Mapped[str]
    causation_id: Mapped[str]
    published_at: Mapped[datetime | None]


class EventOutboxRow(Protocol):
    id: str
    integration_event_name: str
    occurred_at: datetime
    source_service: str
    event_id: str
    aggregate_id: str
    schema_version: int
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    published_at: datetime | None


class EventOutboxToTransportRelay:
    """Publishes pending event outbox rows and marks them published on success."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: EventDeliveryModels,
        transport: IntegrationEventDeliveryTransport,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._outbox_model = cast("type[EventOutboxModel]", models.outbox)
        self._transport = transport
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
                cast("EventOutboxRow", row).published_at = now
            await session.commit()
            return len(rows)

    def _to_envelope(self, row: object) -> IntegrationEventDeliveryEnvelope:
        event_row = cast("EventOutboxRow", row)
        return IntegrationEventDeliveryEnvelope(
            kind="event",
            outbox_id=event_row.id,
            integration_event_name=event_row.integration_event_name,
            occurred_at=event_row.occurred_at,
            payload=event_row.payload,
            correlation_id=event_row.correlation_id,
            causation_id=event_row.causation_id,
            event_id=event_row.event_id,
            source_service=event_row.source_service,
            aggregate_id=event_row.aggregate_id,
            schema_version=event_row.schema_version,
        )