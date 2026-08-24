"""CommandInboxProcessor — consumes inbox commands and dispatches via CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from shell.platform.infrastructure.messaging.inbox.inbox_processor_base import (
    InboxProcessorBase,
)
from shell.platform.infrastructure.serialization.command.deserializer import (
    CommandDeserializer,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
        EnvelopeValidationPolicy,
        EnvelopeValidator,
    )
    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster


class _CommandRow(Protocol):
    id: str
    outbox_id: str
    correlation_id: str
    causation_id: str
    retry_count: int
    schema_version: int
    command_type: str
    payload: dict[str, object]


class CommandInboxProcessor(InboxProcessorBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        command_bus: CommandBus,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_backoff_seconds: int = 30,
        max_retry_backoff_seconds: int = 3600,
        retry_jitter_seconds: float = 0.0,
        lease_duration_seconds: int = 60,
        registry: dict[str, type[object]] | None = None,
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
        *,
        models: CommandDeliveryModels,
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
        self._command_bus = command_bus
        self._deserializer = CommandDeserializer(
            registry=registry or {},
            upcaster=upcaster,
        )

    def _deserialize(self, row: object) -> object | None:
        command_row = cast("_CommandRow", row)
        return self._deserializer.deserialize(
            command_row.command_type,
            getattr(row, "occurred_at", None),
            command_row.payload,
            schema_version=getattr(row, "schema_version", 1),
        )

    async def _dispatch(self, domain_object: object) -> None:
        await self._command_bus.dispatch(domain_object)

    def _causation_value(self, domain_object: object, row: object) -> str:
        return str(getattr(row, "causation_id", ""))

    def _type_name(self, row: object) -> str:
        return cast("_CommandRow", row).command_type
