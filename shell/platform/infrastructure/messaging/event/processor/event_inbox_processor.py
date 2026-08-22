"""EventInboxProcessor — consumes inbox events and triggers application logic via EventBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from shell.platform.infrastructure.messaging.inbox.inbox_processor_base import (
    InboxProcessorBase,
)
from shell.platform.infrastructure.serialization.event.event_deserializer import EventDeserializer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.messaging.event_publisher import EventPublisher
    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
        EnvelopeValidationPolicy,
        EnvelopeValidator,
    )
    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )
    from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
        EventDeliveryModels,
    )
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster


class _EventRow(Protocol):
    id: str
    outbox_id: str
    event_id: str
    source_service: str
    event_type: str
    occurred_at: object
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    aggregate_id: str
    aggregate_name: str
    schema_version: int


class EventInboxProcessor(InboxProcessorBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventPublisher,
        models: EventDeliveryModels,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_backoff_seconds: int = 30,
        max_retry_backoff_seconds: int = 3600,
        retry_jitter_seconds: float = 0.0,
        lease_duration_seconds: int = 60,
        registry: dict[str, type] | None = None,
        worker_id: str | None = None,
        max_concurrency: int = 1,
        envelope_validator: EnvelopeValidator | None = None,
        envelope_policy: EnvelopeValidationPolicy | None = None,
        processed_delivery_model: type[object] | None = None,
        consumer_name: str | None = None,
        heartbeat_interval_seconds: float = 0.0,
        max_batch_time_seconds: float = 0.0,
        upcaster: PayloadUpcaster | None = None,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        super().__init__(
            session_factory,
            cast("type[InboxStateModel]", models.inbox),
            batch_size=batch_size,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            max_retry_backoff_seconds=max_retry_backoff_seconds,
            retry_jitter_seconds=retry_jitter_seconds,
            lease_duration_seconds=lease_duration_seconds,
            worker_id=worker_id,
            max_concurrency=max_concurrency,
            envelope_validator=envelope_validator,
            envelope_policy=envelope_policy,
            processed_delivery_model=processed_delivery_model,
            consumer_name=consumer_name,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            max_batch_time_seconds=max_batch_time_seconds,
            id_generator=id_generator,
        )
        self._event_bus = event_bus
        self._deserializer = EventDeserializer(registry=registry, upcaster=upcaster)

    def _deserialize(self, row: object) -> object | None:
        event_row = cast("_EventRow", row)
        return self._deserializer.deserialize(
            event_row.event_type,
            event_row.occurred_at,  # type: ignore[arg-type]
            event_row.payload,
            schema_version=getattr(row, "schema_version", 1),
            event_id=event_row.event_id,
            correlation_id=event_row.correlation_id,
            causation_id=event_row.causation_id,
            aggregate_id=event_row.aggregate_id,
            aggregate_name=event_row.aggregate_name,
        )

    async def _dispatch(self, domain_object: object) -> None:
        await self._event_bus.publish([domain_object])

    def _causation_value(self, domain_object: object, row: object) -> str:
        event_id = getattr(domain_object, "event_id", None)
        return str(getattr(event_id, "value", event_id))

    def _type_name(self, row: object) -> str:
        return cast("_EventRow", row).event_type
