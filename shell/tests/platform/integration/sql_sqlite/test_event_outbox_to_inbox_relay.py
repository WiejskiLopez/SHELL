"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

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
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.event.event_outbox_to_inbox_relay import (
    EventOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.event.sql_event_outbox_publisher import (
    SqlEventOutboxPublisher,
)
from shell.platform.infrastructure.persistence.memory import FakeEventPublisher
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_OUTBOX_MODEL: Any = EVENT_DELIVERY_MODELS.outbox


class TestEventOutboxToInboxRelay:
    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlEventOutboxPublisher(session_factory, EVENT_DELIVERY_MODELS)
        event = TaskExecutionCreatedEvent.now(
            task_execution_id=TaskExecutionId.generate(),
            now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        )
        await outbox_pub.publish([event])

        downstream = FakeEventPublisher()
        relay = EventOutboxToInboxRelay(session_factory, EVENT_DELIVERY_MODELS, downstream)
        count = await relay.run_once()

        assert count >= 1
        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(_OUTBOX_MODEL).where(_OUTBOX_MODEL.published_at.is_(None))
                    )
                )
                .scalars()
                .all()
            )
        assert all(r.published_at is not None for r in rows)

    async def test_relay_run_twice_idempotent(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlEventOutboxPublisher(session_factory, EVENT_DELIVERY_MODELS)
        await outbox_pub.publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                )
            ]
        )

        downstream = FakeEventPublisher()
        relay = EventOutboxToInboxRelay(session_factory, EVENT_DELIVERY_MODELS, downstream)
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0

    async def test_relay_can_write_to_a_separate_database(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        target_url = f"sqlite+aiosqlite:///{tmp_path / 'target.db'}"
        target_engine = create_async_engine(target_url)
        async with target_engine.begin() as connection:
            await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
        await target_engine.dispose()
        target_session_factory = build_session_factory(target_url)

        outbox_pub = SqlEventOutboxPublisher(session_factory, EVENT_DELIVERY_MODELS)
        await outbox_pub.publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                )
            ]
        )

        relay = EventOutboxToInboxRelay(
            session_factory,
            EVENT_DELIVERY_MODELS,
            target_session_factory=target_session_factory,
            target_models=EVENT_DELIVERY_MODELS,
        )
        assert await relay.run_once() == 1
        assert await relay.run_once() == 0

        async with target_session_factory() as session:
            inbox_rows = (
                (await session.execute(select(EVENT_DELIVERY_MODELS.inbox))).scalars().all()
            )
        assert len(inbox_rows) == 1
