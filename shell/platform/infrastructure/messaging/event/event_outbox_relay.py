"""EventOutboxRelay — reads pending ``event_outbox`` rows and publishes via the event transport."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from shell.platform.application.ports.transport.event_transport import (
    EventDeliveryEnvelope,
)
from shell.platform.infrastructure.messaging.delivery.outbox_relay_base import (
    OutboxRelayBase,
)

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.transport.event_transport import (
        IntegrationEventDeliveryTransport,
    )
    from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
        EventDeliveryModels,
    )


class EventOutboxRow(Protocol):
    event_id: str
    integration_event_name: str
    occurred_at: datetime
    source_service: str
    aggregate_id: str
    schema_version: int
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    published_at: datetime | None


class EventOutboxRelay(OutboxRelayBase):
    """Publishes pending event outbox rows and marks them published on success."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: EventDeliveryModels,
        transport: IntegrationEventDeliveryTransport,
        batch_size: int = 100,
    ) -> None:
        super().__init__(session_factory, transport, batch_size)
        self._models = models

    @property
    def outbox_model(self) -> type[Any]:
        return self._models.outbox

    @property
    def order_column(self) -> Any:
        return self._models.outbox.occurred_at

    def _to_envelope(self, row: object) -> EventDeliveryEnvelope:
        event_row = cast("EventOutboxRow", row)
        return EventDeliveryEnvelope(
            event_id=event_row.event_id,
            contract_type=event_row.integration_event_name,
            occurred_at=event_row.occurred_at,
            aggregate_id=event_row.aggregate_id,
            schema_version=event_row.schema_version,
            source_service=event_row.source_service,
            destination_service="*",
            correlation_id=event_row.correlation_id,
            causation_id=event_row.causation_id,
            payload=event_row.payload,
        )