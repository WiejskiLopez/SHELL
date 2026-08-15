"""SQLite integration tests for the refactored EventInboxProcessor (claim→process→ack)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import insert, select

from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
)
from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.context import get_causation_id, get_correlation_id
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    UNSUPPORTED_SCHEMA_VERSION,
    EnvelopeValidationPolicy,
    EnvelopeValidator,
)
from shell.platform.infrastructure.serialization import DomainEventSerializer
from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import async_sessionmaker

_INBOX_MODEL: Any = EVENT_DELIVERY_MODELS.inbox


def _event() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


class CollectingBus:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.items: list[object] = []

    async def publish(self, items: Sequence[object]) -> None:
        if self.fail:
            raise RuntimeError("publish failed")
        self.items.extend(items)


async def _add_event(
    session_factory: async_sessionmaker,
    event_id: str,
    *,
    event: TaskExecutionCreatedEvent | None = None,
    status: str = InboxStatus.PENDING.value,
) -> None:
    event = event or _event()
    serializer = DomainEventSerializer()
    async with session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.inbox(
                id=event_id,
                event_type=type(event).__name__,
                occurred_at=event.occurred_at.value,
                payload=serializer.to_payload(event),
                correlation_id="corr",
                causation_id="cause",
                received_at=datetime.now(tz=UTC),
                status=status,
            )
        )
        await session.commit()


async def _read_row(
    session_factory: async_sessionmaker,
    event_id: str,
) -> Any:
    async with session_factory() as session:
        row = (
            await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == event_id))
        ).scalar_one()
        return row


class TestEventInboxProcessorRefactored:
    async def test_success_marks_processed(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-ok", event=event)
        bus = CollectingBus()
        processor = EventInboxProcessor(
            session_factory,
            bus,
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
        )
        result = await processor.run_once()

        assert result.claimed_count == 1
        assert result.processed_count == 1
        assert result.failed_count == 0
        assert len(bus.items) == 1

        row = await _read_row(session_factory, "evt-ok")
        assert row.status == InboxStatus.PROCESSED.value
        assert row.processed_at is not None
        assert row.claimed_by is None
        assert row.lease_until is None

    async def test_second_run_claims_nothing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-once", event=event)
        processor = EventInboxProcessor(
            session_factory,
            CollectingBus(),
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
        )
        first = await processor.run_once()
        second = await processor.run_once()
        assert first.processed_count == 1
        assert second.claimed_count == 0

    async def test_handler_failure_retries_then_dlq(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-fail", event=event)
        processor = EventInboxProcessor(
            session_factory,
            CollectingBus(fail=True),
            max_retries=2,
            retry_backoff_seconds=0,
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
        )
        first = await processor.run_once()
        row = await _read_row(session_factory, "evt-fail")
        assert first.retried_count == 1
        assert row.status == InboxStatus.RETRY.value
        assert row.retry_count == 1
        assert row.error_code == "HANDLER_ERROR"

        second = await processor.run_once()
        row = await _read_row(session_factory, "evt-fail")
        assert second.dead_lettered_count == 1
        assert row.status == InboxStatus.DEAD_LETTER.value
        assert row.retry_count == 2
        assert row.failed_at is not None

    async def test_deserialization_error_goes_to_dlq_after_retries(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-unknown", event=event)
        processor = EventInboxProcessor(
            session_factory,
            CollectingBus(),
            max_retries=2,
            retry_backoff_seconds=0,
            models=EVENT_DELIVERY_MODELS,
            registry={},  # unknown type
        )
        first = await processor.run_once()
        row = await _read_row(session_factory, "evt-unknown")
        assert first.retried_count == 1
        assert row.status == InboxStatus.RETRY.value
        assert row.error_code == "DESERIALIZATION_ERROR"

        await processor.run_once()
        row = await _read_row(session_factory, "evt-unknown")
        assert row.status == InboxStatus.DEAD_LETTER.value
        assert row.retry_count == 2

    async def test_lost_lease_is_not_acknowledged(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-leased", event=event)
        # Pre-claim the record as another worker's lease so the processor cannot ack.
        async with session_factory() as session:
            row = (
                await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == "evt-leased"))
            ).scalar_one()
            row.status = InboxStatus.PROCESSING.value
            row.claimed_by = "other-worker"
            row.lease_until = datetime.now(tz=UTC) + timedelta(minutes=5)
            await session.commit()

        processor = EventInboxProcessor(
            session_factory,
            CollectingBus(),
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
        )
        result = await processor.run_once()
        assert result.claimed_count == 0

    async def test_recovers_expired_lease_of_other_worker(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-stale", event=event)
        async with session_factory() as session:
            row = (
                await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == "evt-stale"))
            ).scalar_one()
            row.status = InboxStatus.PROCESSING.value
            row.claimed_by = "dead-worker"
            row.lease_until = datetime.now(tz=UTC) - timedelta(minutes=5)
            await session.commit()

        bus = CollectingBus()
        processor = EventInboxProcessor(
            session_factory,
            bus,
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
        )
        result = await processor.run_once()
        assert result.claimed_count == 1
        assert result.processed_count == 1
        assert len(bus.items) == 1

    async def test_duplicate_delivery_id_is_processed_once(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        serializer = DomainEventSerializer()
        payload = serializer.to_payload(event)
        now = datetime.now(tz=UTC)
        async with session_factory() as session:
            session.add(
                EVENT_DELIVERY_MODELS.inbox(
                    id="evt-dup",
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at.value,
                    payload=payload,
                    correlation_id="corr",
                    causation_id="cause",
                    received_at=now,
                )
            )
            # Same delivery id delivered twice (idempotent inbox insert,
            # mirroring the relay's ON CONFLICT DO NOTHING / OR IGNORE).
            await session.execute(
                insert(EVENT_DELIVERY_MODELS.inbox)
                .values(
                    id="evt-dup",
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at.value,
                    payload=payload,
                    correlation_id="corr",
                    causation_id="cause",
                    received_at=now,
                )
                .prefix_with("OR IGNORE")
            )
            await session.commit()

        bus = CollectingBus()
        processor = EventInboxProcessor(
            session_factory,
            bus,
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
        )
        result = await processor.run_once()
        assert result.claimed_count == 1
        assert result.processed_count == 1
        assert len(bus.items) == 1

    async def test_restart_after_handler_before_ack_reprocesses(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        """Simulates a worker crash after the handler ran but before the ack.

        The record stays ``PROCESSING`` until its lease expires; a new worker
        reclaims it and the handler runs again (at-least-once delivery). The
        handler is responsible for idempotency.
        """
        event = _event()
        await _add_event(session_factory, "evt-crash", event=event)

        # Worker A claims and processes but dies before ack: lease left expired.
        async with session_factory() as session:
            row = (
                await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == "evt-crash"))
            ).scalar_one()
            row.status = InboxStatus.PROCESSING.value
            row.claimed_by = "worker-a"
            row.lease_until = datetime.now(tz=UTC) - timedelta(minutes=5)
            await session.commit()

        # Worker B reclaims the expired lease and processes again.
        bus = CollectingBus()
        processor = EventInboxProcessor(
            session_factory,
            bus,
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
        )
        result = await processor.run_once()
        assert result.claimed_count == 1
        assert result.processed_count == 1
        assert len(bus.items) == 1

        row = await _read_row(session_factory, "evt-crash")
        assert row.status == InboxStatus.PROCESSED.value
        assert row.claimed_by is None


class ContextCapturingBus:
    """Captures the correlation and causation ids seen inside each publish call."""

    def __init__(self) -> None:
        self.observed_correlation: list[str] = []
        self.observed_causation: list[str] = []

    async def publish(self, items: Sequence[object]) -> None:
        for _item in items:
            self.observed_correlation.append(get_correlation_id())
            self.observed_causation.append(get_causation_id())


class TestEventInboxProcessorConcurrency:
    async def test_concurrent_records_keep_isolated_context(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event_a = _event()
        event_b = _event()
        serializer = DomainEventSerializer()
        async with session_factory() as session:
            for event_id, event, causation in (
                ("evt-a", event_a, "cause-a"),
                ("evt-b", event_b, "cause-b"),
            ):
                session.add(
                    EVENT_DELIVERY_MODELS.inbox(
                        id=event_id,
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at.value,
                        payload=serializer.to_payload(event),
                        correlation_id=f"corr-{event_id}",
                        causation_id=causation,
                        received_at=datetime.now(tz=UTC),
                    )
                )
            await session.commit()

        bus = ContextCapturingBus()
        processor = EventInboxProcessor(
            session_factory,
            bus,
            models=EVENT_DELIVERY_MODELS,
            registry={type(event_a).__name__: type(event_a)},
            max_concurrency=2,
            heartbeat_interval_seconds=10,
        )
        result = await processor.run_once()
        assert result.claimed_count == 2
        assert result.processed_count == 2
        assert sorted(bus.observed_correlation) == ["corr-evt-a", "corr-evt-b"]
        assert len(bus.observed_causation) == 2
        assert len(set(bus.observed_causation)) == 2, (
            "each concurrent record must trace its own causation id"
        )


class TestEventInboxProcessorEnvelopeValidation:
    async def test_unsupported_schema_version_goes_to_dlq(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-ver", event=event)
        # Force an unsupported schema version on the record.
        async with session_factory() as session:
            row = (
                await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == "evt-ver"))
            ).scalar_one()
            row.schema_version = 99
            await session.commit()

        processor = EventInboxProcessor(
            session_factory,
            CollectingBus(),
            models=EVENT_DELIVERY_MODELS,
            registry={type(event).__name__: type(event)},
            envelope_validator=EnvelopeValidator(
                EnvelopeValidationPolicy(
                    supported_schema_versions={type(event).__name__: frozenset({1})}
                )
            ),
        )
        result = await processor.run_once()
        assert result.dead_lettered_count == 1

        row = await _read_row(session_factory, "evt-ver")
        assert row.status == InboxStatus.DEAD_LETTER.value
        assert row.error_code == UNSUPPORTED_SCHEMA_VERSION


class TestEventInboxProcessorUpcasting:
    async def test_upcasts_older_schema_and_dead_letters_newer(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        """One batch: a v1 payload is upcast and processed, a v99 payload goes to DLQ."""
        task_id = TaskExecutionId.generate()
        now = datetime.now(tz=UTC)
        async with session_factory() as session:
            session.add(
                _INBOX_MODEL(
                    id="evt-upcast-v1",
                    event_type=TaskExecutionCreatedEvent.__name__,
                    occurred_at=now,
                    payload={"task_execution_id": str(task_id.value)},
                    correlation_id="corr",
                    causation_id="cause",
                    received_at=now,
                    status=InboxStatus.PENDING.value,
                    schema_version=1,
                )
            )
            session.add(
                _INBOX_MODEL(
                    id="evt-upcast-future",
                    event_type=TaskExecutionCreatedEvent.__name__,
                    occurred_at=now,
                    payload={"task_execution_id": str(task_id.value)},
                    correlation_id="corr",
                    causation_id="cause",
                    received_at=now,
                    status=InboxStatus.PENDING.value,
                    schema_version=99,
                )
            )
            await session.commit()

        upcaster = PayloadUpcaster(
            {
                TaskExecutionCreatedEvent.__name__: {
                    1: (
                        lambda p: {
                            "task_execution_id": TaskExecutionId(str(p["task_execution_id"]))
                        }
                    ),
                }
            }
        )
        processor = EventInboxProcessor(
            session_factory,
            CollectingBus(),
            models=EVENT_DELIVERY_MODELS,
            registry={TaskExecutionCreatedEvent.__name__: TaskExecutionCreatedEvent},
            upcaster=upcaster,
            envelope_validator=EnvelopeValidator(
                EnvelopeValidationPolicy(
                    supported_schema_versions={
                        TaskExecutionCreatedEvent.__name__: frozenset({1, 2})
                    }
                )
            ),
            heartbeat_interval_seconds=10,
        )
        result = await processor.run_once()

        assert result.processed_count == 1
        assert result.dead_lettered_count == 1

        row_v1 = await _read_row(session_factory, "evt-upcast-v1")
        assert row_v1.status == InboxStatus.PROCESSED.value
        row_future = await _read_row(session_factory, "evt-upcast-future")
        assert row_future.status == InboxStatus.DEAD_LETTER.value
        assert row_future.error_code == UNSUPPORTED_SCHEMA_VERSION
