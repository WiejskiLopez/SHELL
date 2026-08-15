"""Faza 1 tests — atomic handler + outbox + ack, rollback semantics, dedup.

Verifies the session-scope transaction guarantees (ref2.md §4.1):

- a successful processing commit persists the handler change, the outbox row and
  the ``PROCESSED`` status in one transaction;
- an explicit handler rollback inside the deferred scope aborts the whole
  transaction: nothing is committed, the inbox is scheduled for retry, and no
  outbox row is written;
- a ``processed_delivery`` row makes a redelivery a no-op (dispatch skipped).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from sqlalchemy import select

from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.inbox_status import InboxStatus
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)
from shell.platform.infrastructure.serialization import DomainEventSerializer
from shell.tests.platform.integration.platform_delivery_models import (
    EVENT_DELIVERY_MODELS,
    PERSISTENCE_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import async_sessionmaker

_INBOX_MODEL: Any = EVENT_DELIVERY_MODELS.inbox


def _event() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


class StagingBus:
    """Dispatches every published item to a single handler and records calls."""

    def __init__(self, handler: object) -> None:
        self._handler = handler
        self.items: list[object] = []

    async def publish(self, items: Sequence[object]) -> None:
        for item in items:
            self.items.append(item)
            await self._handler.handle(item)  # type: ignore[attr-defined]


async def _add_event(
    session_factory: async_sessionmaker,
    event_id: str,
    *,
    event: TaskExecutionCreatedEvent,
) -> None:
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
                status=InboxStatus.PENDING.value,
            )
        )
        await session.commit()


def _processor(
    session_factory: async_sessionmaker,
    bus: StagingBus,
    *,
    event: TaskExecutionCreatedEvent,
    consumer_name: str | None = None,
) -> EventInboxProcessor:
    return EventInboxProcessor(
        session_factory,
        bus,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
        processed_delivery_model=(
            PERSISTENCE_DELIVERY_MODELS.processed_delivery if consumer_name else None
        ),
        consumer_name=consumer_name,
    )


async def _inbox_row(session_factory: async_sessionmaker, event_id: str) -> Any:
    async with session_factory() as session:
        row = (
            await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == event_id))
        ).scalar_one()
        return row


async def _outbox_rows(session_factory: async_sessionmaker) -> list[Any]:
    async with session_factory() as session:
        rows = (
            (await session.execute(select(PERSISTENCE_DELIVERY_MODELS.events.outbox)))
            .scalars()
            .all()
        )
        return list(rows)


class TestAtomicity:
    async def test_success_commits_change_outbox_and_ack_together(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-atomic", event=event)

        class CommitHandler:
            def __init__(self, uow: SqlAlchemyUnitOfWorkBase) -> None:
                self._uow = uow

            async def handle(self, item: object) -> None:
                async with self._uow as uow:
                    uow.stage_events([item])

        uow = SqlAlchemyUnitOfWorkBase(
            session_factory,
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        bus = StagingBus(CommitHandler(uow))
        baseline = len(await _outbox_rows(session_factory))
        result = await _processor(session_factory, bus, event=event).run_once()

        assert result.processed_count == 1
        assert len(bus.items) == 1
        assert len(await _outbox_rows(session_factory)) == baseline + 1
        row = await _inbox_row(session_factory, "evt-atomic")
        assert row.status == InboxStatus.PROCESSED.value

    async def test_handler_rollback_aborts_transaction_and_schedules_retry(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-rollback", event=event)

        class RollbackHandler:
            def __init__(self, uow: SqlAlchemyUnitOfWorkBase) -> None:
                self._uow = uow

            async def handle(self, item: object) -> None:
                async with self._uow as uow:
                    uow.stage_events([item])
                    await uow.rollback()

        uow = SqlAlchemyUnitOfWorkBase(
            session_factory,
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        bus = StagingBus(RollbackHandler(uow))
        baseline = len(await _outbox_rows(session_factory))
        result = await _processor(session_factory, bus, event=event).run_once()

        assert result.processed_count == 0
        assert result.retried_count == 1
        assert len(bus.items) == 1, "handler ran once before rolling back"
        assert len(await _outbox_rows(session_factory)) == baseline, "outbox must not be committed"
        row = await _inbox_row(session_factory, "evt-rollback")
        assert row.status == InboxStatus.RETRY.value
        assert row.error_code == "HANDLER_ERROR"


class TestProcessedDeliveryDedup:
    async def test_processed_delivery_skips_dispatch_and_acks(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-dedup", event=event)

        async with session_factory() as session:
            session.add(
                PERSISTENCE_DELIVERY_MODELS.processed_delivery(
                    id=str(uuid4()),
                    consumer_name="test-consumer",
                    delivery_id="evt-dedup",
                    payload={},
                    processed_at=datetime.now(tz=UTC),
                )
            )
            await session.commit()

        bus = StagingBus(handler=_NoopHandler())
        result = await _processor(
            session_factory,
            bus,
            event=event,
            consumer_name="test-consumer",
        ).run_once()

        assert result.processed_count == 1
        assert len(bus.items) == 0, "duplicate delivery must not re-dispatch the handler"
        row = await _inbox_row(session_factory, "evt-dedup")
        assert row.status == InboxStatus.PROCESSED.value

    async def test_different_consumer_still_dispatches(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-other-consumer", event=event)

        async with session_factory() as session:
            session.add(
                PERSISTENCE_DELIVERY_MODELS.processed_delivery(
                    id=str(uuid4()),
                    consumer_name="other-consumer",
                    delivery_id="evt-other-consumer",
                    payload={},
                    processed_at=datetime.now(tz=UTC),
                )
            )
            await session.commit()

        bus = StagingBus(handler=_NoopHandler())
        result = await _processor(
            session_factory,
            bus,
            event=event,
            consumer_name="test-consumer",
        ).run_once()

        assert result.processed_count == 1
        assert len(bus.items) == 1, "a different consumer must still process the delivery"


class TestProcessedDeliveryAtomicWrite:
    """The dedup row is written atomically with the effect, outbox and ack.

    After a successful processing run, a ``processed_delivery`` row exists for the
    same consumer — so a replay or redelivery is a no-op and never re-runs the
    handler (ref2.md §4.1, ref4.md Krok 1).
    """

    async def test_success_records_processed_delivery_with_effect(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-dedup-atomic", event=event)

        uow = SqlAlchemyUnitOfWorkBase(
            session_factory,
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        bus = StagingBus(_CommitHandler(uow))
        baseline = len(await _outbox_rows(session_factory))
        result = await _processor(
            session_factory,
            bus,
            event=event,
            consumer_name="test-consumer",
        ).run_once()

        assert result.processed_count == 1
        assert len(bus.items) == 1
        assert len(await _outbox_rows(session_factory)) == baseline + 1
        row = await _inbox_row(session_factory, "evt-dedup-atomic")
        assert row.status == InboxStatus.PROCESSED.value

        async with session_factory() as session:
            dedup_model = cast("Any", PERSISTENCE_DELIVERY_MODELS.processed_delivery)
            dedup = (
                (
                    await session.execute(
                        select(dedup_model).where(dedup_model.delivery_id == "evt-dedup-atomic")
                    )
                )
                .scalars()
                .all()
            )
        assert len(dedup) == 1
        assert dedup[0].consumer_name == "test-consumer"

    async def test_replayed_record_does_not_re_dispatch(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        event = _event()
        await _add_event(session_factory, "evt-dedup-replay", event=event)

        first_uow = SqlAlchemyUnitOfWorkBase(
            session_factory,
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        first_bus = StagingBus(_CommitHandler(first_uow))
        baseline = len(await _outbox_rows(session_factory))
        result = await _processor(
            session_factory,
            first_bus,
            event=event,
            consumer_name="test-consumer",
        ).run_once()
        assert result.processed_count == 1
        assert len(first_bus.items) == 1
        assert len(await _outbox_rows(session_factory)) == baseline + 1

        # Simulate an operator replay of the already-PROCESSED record: reset it
        # to PENDING without touching the business data.
        async with session_factory() as session:
            row = (
                await session.execute(
                    select(_INBOX_MODEL).where(_INBOX_MODEL.id == "evt-dedup-replay")
                )
            ).scalar_one()
            row.status = InboxStatus.PENDING.value
            row.claimed_by = None
            row.lease_until = None
            await session.commit()

        second_uow = SqlAlchemyUnitOfWorkBase(
            session_factory,
            models=PERSISTENCE_DELIVERY_MODELS,
        )
        second_bus = StagingBus(_CommitHandler(second_uow))
        second_result = await _processor(
            session_factory,
            second_bus,
            event=event,
            consumer_name="test-consumer",
        ).run_once()

        assert second_result.processed_count == 1
        assert len(second_bus.items) == 0, "dedup row must prevent re-dispatch"
        assert len(await _outbox_rows(session_factory)) == baseline + 1, (
            "replay must not create a second outbox/audit effect"
        )
        row = await _inbox_row(session_factory, "evt-dedup-replay")
        assert row.status == InboxStatus.PROCESSED.value


class _NoopHandler:
    async def handle(self, item: object) -> None:  # noqa: ARG002
        return None


class _CommitHandler:
    """Stages the dispatched item into the processing UoW (shared session)."""

    def __init__(self, uow: SqlAlchemyUnitOfWorkBase) -> None:
        self._uow = uow

    async def handle(self, item: object) -> None:
        async with self._uow as uow:
            uow.stage_events([item])
