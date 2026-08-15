"""System tests — full outbox → transport → inbox → processor → outbox flow.

Uses two separate SQLite databases (producer BC and consumer BC) and a transport
test double (the outbox-to-inbox relay with a separate target session), then runs
the consumer inbox processor. Verifies at-least-once delivery, retry→DLQ,
duplicate suppression, replay and worker restart behaviour across the whole pipe.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

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
from shell.platform.infrastructure.messaging.event.event_outbox_to_inbox_relay import (
    EventOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.event.sql_event_outbox_publisher import (
    SqlEventOutboxPublisher,
)
from shell.platform.infrastructure.messaging.inbox import InboxReplayService
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import InboxStateModel

_INBOX_MODEL: type[InboxStateModel] = cast("type[InboxStateModel]", EVENT_DELIVERY_MODELS.inbox)


def _event() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


class RecordingBus:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.items: list[object] = []

    async def publish(self, items: Sequence[object]) -> None:
        if self.fail:
            raise RuntimeError("publish failed")
        self.items.extend(items)


async def _build_pair(
    tmp_path,
) -> tuple[
    async_sessionmaker,
    async_sessionmaker,
    EventOutboxToInboxRelay,
]:
    producer_url = f"sqlite+aiosqlite:///{tmp_path / 'producer.db'}"
    consumer_url = f"sqlite+aiosqlite:///{tmp_path / 'consumer.db'}"

    producer_engine = create_async_engine(producer_url)
    consumer_engine = create_async_engine(consumer_url)
    async with producer_engine.begin() as connection:
        await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
    async with consumer_engine.begin() as connection:
        await connection.run_sync(EVENT_DELIVERY_MODELS.inbox.metadata.create_all)
    await producer_engine.dispose()
    await consumer_engine.dispose()

    producer = build_session_factory(producer_url)
    consumer = build_session_factory(consumer_url)

    relay = EventOutboxToInboxRelay(
        producer,
        models=EVENT_DELIVERY_MODELS,
        target_session_factory=consumer,
        target_models=EVENT_DELIVERY_MODELS,
    )
    return producer, consumer, relay


async def test_end_to_end_delivery_and_processing(tmp_path) -> None:
    producer, consumer, relay = await _build_pair(tmp_path)
    event = _event()
    await SqlEventOutboxPublisher(producer, EVENT_DELIVERY_MODELS).publish([event])

    assert await relay.run_once() == 1
    assert await relay.run_once() == 0  # no second delivery

    bus = RecordingBus()
    processor = EventInboxProcessor(
        consumer,
        bus,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    result = await processor.run_once()
    assert result.processed_count == 1
    assert len(bus.items) == 1

    async with consumer() as session:
        rows = (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == InboxStatus.PROCESSED.value


async def test_retry_then_dlq_across_restart(tmp_path) -> None:
    producer, consumer, relay = await _build_pair(tmp_path)
    event = _event()
    await SqlEventOutboxPublisher(producer, EVENT_DELIVERY_MODELS).publish([event])
    await relay.run_once()

    # First processor instance fails the handler; second (restarted) instance
    # retries the same record and finally dead-letters it.
    failing = EventInboxProcessor(
        consumer,
        RecordingBus(fail=True),
        max_retries=2,
        retry_backoff_seconds=0,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    assert (await failing.run_once()).retried_count == 1

    restarted = EventInboxProcessor(
        consumer,
        RecordingBus(fail=True),
        max_retries=2,
        retry_backoff_seconds=0,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    assert (await restarted.run_once()).dead_lettered_count == 1

    async with consumer() as session:
        rows = (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == InboxStatus.DEAD_LETTER.value
    assert rows[0].retry_count == 2
    assert rows[0].error_code == "HANDLER_ERROR"


async def test_replay_after_restart_reprocesses_dead_letter(tmp_path) -> None:
    producer, consumer, relay = await _build_pair(tmp_path)
    event = _event()
    await SqlEventOutboxPublisher(producer, EVENT_DELIVERY_MODELS).publish([event])
    await relay.run_once()

    failing = EventInboxProcessor(
        consumer,
        RecordingBus(fail=True),
        max_retries=1,
        retry_backoff_seconds=0,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    assert (await failing.run_once()).dead_lettered_count == 1

    async with consumer() as session:
        rows = (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
    delivery_id = rows[0].id
    assert rows[0].status == InboxStatus.DEAD_LETTER.value

    # Operator replays the DLQ delivery; a fresh processor handles it.
    replay = InboxReplayService(consumer, _INBOX_MODEL)
    assert await replay.replay_by_id(delivery_id, operator="ops", reason="fixed") is True

    bus = RecordingBus()
    restarted = EventInboxProcessor(
        consumer,
        bus,
        max_retries=1,
        retry_backoff_seconds=0,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    assert (await restarted.run_once()).processed_count == 1
    assert len(bus.items) == 1

    async with consumer() as session:
        rows = (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
    assert rows[0].status == InboxStatus.PROCESSED.value


async def test_full_lifecycle_success_duplicate_retry_dlq_restart(tmp_path) -> None:
    """One end-to-end test: success, duplicate no-op, retry, DLQ and restart.

    Exercises the whole pipe on two independent databases (ref4.md Krok 7):
    outbox → relay → inbox → processor, with an idempotent consumer, an at-least
    -once redelivery, a failing handler (retry → DLQ) and a restarted worker that
    replays the dead-lettered record.
    """
    producer, consumer, relay = await _build_pair(tmp_path)

    # ── 1. Success ─────────────────────────────────────────────────────
    event = _event()
    await SqlEventOutboxPublisher(producer, EVENT_DELIVERY_MODELS).publish([event])
    assert await relay.run_once() == 1
    assert await relay.run_once() == 0  # relay-level dedup: no second delivery

    ok_bus = RecordingBus()
    ok = EventInboxProcessor(
        consumer,
        ok_bus,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    assert (await ok.run_once()).processed_count == 1
    assert len(ok_bus.items) == 1, "exactly one business effect"

    # ── 2. Duplicate redelivery is a no-op ─────────────────────────────
    # The record is already PROCESSED, so a second pass claims nothing.
    dup_bus = RecordingBus()
    dup = EventInboxProcessor(
        consumer,
        dup_bus,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event).__name__: type(event)},
    )
    assert (await dup.run_once()).claimed_count == 0
    assert len(dup_bus.items) == 0, "duplicate delivery must not create a second effect"

    # ── 3. Retry → DLQ across a worker restart ─────────────────────────
    event2 = _event()
    await SqlEventOutboxPublisher(producer, EVENT_DELIVERY_MODELS).publish([event2])
    assert await relay.run_once() == 1

    failing = EventInboxProcessor(
        consumer,
        RecordingBus(fail=True),
        max_retries=2,
        retry_backoff_seconds=0,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event2).__name__: type(event2)},
    )
    assert (await failing.run_once()).retried_count == 1

    restarted = EventInboxProcessor(
        consumer,
        RecordingBus(fail=True),
        max_retries=2,
        retry_backoff_seconds=0,
        models=EVENT_DELIVERY_MODELS,
        registry={type(event2).__name__: type(event2)},
    )
    assert (await restarted.run_once()).dead_lettered_count == 1

    async with consumer() as session:
        rows = (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
    by_type = {row.event_type: row for row in rows}
    failed_row = by_type[type(event2).__name__]
    assert failed_row.status == InboxStatus.DEAD_LETTER.value
    assert failed_row.error_code == "HANDLER_ERROR"

    # ── 4. Restart replays the DLQ record to success ───────────────────
    replay = InboxReplayService(consumer, _INBOX_MODEL)
    assert await replay.replay_by_id(failed_row.id, operator="ops", reason="fixed") is True

    recovered = EventInboxProcessor(
        consumer,
        RecordingBus(),
        models=EVENT_DELIVERY_MODELS,
        registry={type(event2).__name__: type(event2)},
    )
    assert (await recovered.run_once()).processed_count == 1

    async with consumer() as session:
        rows = (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
    recovered_row = next(row for row in rows if row.id == failed_row.id)
    assert recovered_row.status == InboxStatus.PROCESSED.value
