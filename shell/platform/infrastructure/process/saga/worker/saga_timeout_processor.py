"""SagaTimeoutProcessor — odpalanie timeoutów sag przez reużycie InboxProcessorBase.

Claimuje rekordy ``saga_timeout`` (po ``next_attempt_at = due_at``), dispatches
event ``SagaTimedOut`` na EventBus i akceptuje w tej samej transakcji. Retry,
backoff, DLQ, heartbeat i reclaim po awarii są dziedziczone z
``InboxProcessorBase`` bez nowego kodu.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from shell.platform.infrastructure.messaging.inbox.inbox_processor_base import (
    InboxProcessorBase,
)
from shell.platform.process.saga.saga_timed_out import SagaTimedOut

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
    from shell.platform.infrastructure.process.saga.models.saga_delivery import (
        SagaDeliveryModels,
    )
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster


class _TimeoutRow(Protocol):
    """Runtime instance shape of a claimed saga_timeout row."""

    saga_id: str
    saga_key: str
    step: str


class SagaTimeoutProcessor(InboxProcessorBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventPublisher,
        models: SagaDeliveryModels,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_backoff_seconds: int = 30,
        max_retry_backoff_seconds: int = 3600,
        retry_jitter_seconds: float = 0.0,
        lease_duration_seconds: int = 60,
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
            cast("type[InboxStateModel]", models.timeout),
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

    def _deserialize(self, row: object) -> object | None:
        timeout_row = cast("_TimeoutRow", row)
        return SagaTimedOut(
            saga_id=timeout_row.saga_id,
            saga_key=timeout_row.saga_key,
            step=timeout_row.step,
            payload=dict(getattr(timeout_row, "payload", None) or {}),
        )

    async def _dispatch(self, domain_object: object) -> None:
        await self._event_bus.publish([domain_object])

    def _causation_value(self, domain_object: object, row: object) -> str:
        return str(getattr(row, "outbox_id", ""))

    def _message_name(self, row: object) -> str:
        return "saga_timeout"
