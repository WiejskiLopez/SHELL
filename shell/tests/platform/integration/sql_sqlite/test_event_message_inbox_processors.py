"""SQLite integration tests for event and message inbox processors."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from shell.execution.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.payloads.ingestion_payload import (
    IngestionPayload,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.ingestion.infrastructure.ingestion.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
    MESSAGE_DELIVERY_MODELS,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.message.processor.message_inbox_processor import (
    MessageInboxProcessor,
)
from shell.platform.infrastructure.serialization import (
    DomainEventSerializer,
    DomainMessageSerializer,
)
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import async_sessionmaker

_EVENT_INBOX_MODEL: Any = EVENT_DELIVERY_MODELS.inbox
_MESSAGE_INBOX_MODEL: Any = MESSAGE_DELIVERY_MODELS.inbox


def _event() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


def _message() -> IngestionPayload:
    return IngestionPayload(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
    )


class CollectingBus:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.items: list[object] = []

    async def publish(self, items: Sequence[object]) -> None:
        if self.fail:
            raise RuntimeError("publish failed")
        self.items.extend(items)


async def test_event_processor_success_marks_inbox_processed(
    session_factory: async_sessionmaker,
) -> None:
    event = _event()
    serializer = DomainEventSerializer()
    async with session_factory() as session:
        session.add(
            EVENT_DELIVERY_MODELS.inbox(
                id="event-processor-success",
                event_type=type(event).__name__,
                occurred_at=event.occurred_at.value,
                payload=serializer.to_payload(event),
                correlation_id="corr-event",
                causation_id="cause-event",
                received_at=datetime.now(tz=UTC),
            )
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
    assert result.failed_count == 0
    assert len(bus.items) == 1

    async with session_factory() as session:
        row = (
            await session.execute(
                select(_EVENT_INBOX_MODEL).where(_EVENT_INBOX_MODEL.id == "event-processor-success")
            )
        ).scalar_one()
    assert row.processed_at is not None
    assert row.retry_count == 0


async def test_message_processor_failure_retries_then_dlq(
    session_factory: async_sessionmaker,
) -> None:
    message = _message()
    serializer = DomainMessageSerializer()
    async with session_factory() as session:
        session.add(
            MESSAGE_DELIVERY_MODELS.inbox(
                id="message-processor-dlq",
                message_type=type(message).__name__,
                occurred_at=message.occurred_at.value,
                payload=serializer.to_payload(message),
                correlation_id="corr-message",
                causation_id="cause-message",
                received_at=datetime.now(tz=UTC),
            )
        )
        await session.commit()

    processor = MessageInboxProcessor(
        session_factory,
        CollectingBus(fail=True),
        max_retries=2,
        retry_backoff_seconds=0,
        models=MESSAGE_DELIVERY_MODELS,
        registry={type(message).__name__: type(message)},
    )
    first = await processor.run_once()
    assert first.retried_count == 1
    second = await processor.run_once()
    assert second.dead_lettered_count == 1

    async with session_factory() as session:
        row = (
            await session.execute(
                select(_MESSAGE_INBOX_MODEL).where(
                    _MESSAGE_INBOX_MODEL.id == "message-processor-dlq"
                )
            )
        ).scalar_one()
    assert row.processed_at is None
    assert row.retry_count == 2
    assert row.error_code == "HANDLER_ERROR"
    assert row.failed_at is not None
