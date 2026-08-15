"""SQLite integration tests — message outbox publisher and relay."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.ingestion.domain.ingestion.aggregates.ingestion.payloads.ingestion_payload import (
    IngestionPayload,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.ingestion.infrastructure.ingestion.persistence.sql.models.base import (
    MESSAGE_DELIVERY_MODELS,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.message.message_outbox_to_inbox_relay import (
    MessageOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.message.sql_message_outbox_publisher import (
    SqlMessageOutboxPublisher,
)
from shell.platform.infrastructure.persistence.memory.fake_message_publisher import (
    FakeMessagePublisher,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_OUTBOX_MODEL: Any = MESSAGE_DELIVERY_MODELS.outbox


def _ingestion_payload() -> IngestionPayload:
    return IngestionPayload(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
    )


class TestMessageOutboxToInboxRelay:
    async def test_relay_uses_injected_ingestion_models(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlMessageOutboxPublisher(session_factory, MESSAGE_DELIVERY_MODELS)
        await outbox_pub.publish([_ingestion_payload()])

        relay = MessageOutboxToInboxRelay(
            session_factory,
            models=MESSAGE_DELIVERY_MODELS,
        )
        assert await relay.run_once() >= 1

        async with session_factory() as session:
            rows = (await session.execute(select(MESSAGE_DELIVERY_MODELS.outbox))).scalars().all()
        assert rows
        assert all(row.published_at is not None for row in rows)

    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlMessageOutboxPublisher(session_factory, MESSAGE_DELIVERY_MODELS)
        await outbox_pub.publish([_ingestion_payload()])

        downstream = FakeMessagePublisher()
        relay = MessageOutboxToInboxRelay(
            session_factory,
            downstream,
            models=MESSAGE_DELIVERY_MODELS,
        )
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
        outbox_pub = SqlMessageOutboxPublisher(session_factory, MESSAGE_DELIVERY_MODELS)
        await outbox_pub.publish([_ingestion_payload()])

        downstream = FakeMessagePublisher()
        relay = MessageOutboxToInboxRelay(
            session_factory,
            downstream,
            models=MESSAGE_DELIVERY_MODELS,
        )
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0

    async def test_relay_can_write_to_a_separate_database(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        target_url = f"sqlite+aiosqlite:///{tmp_path / 'target-message.db'}"
        target_engine = create_async_engine(target_url)
        async with target_engine.begin() as connection:
            await connection.run_sync(MESSAGE_DELIVERY_MODELS.outbox.metadata.create_all)
        await target_engine.dispose()
        target_session_factory = build_session_factory(target_url)

        outbox_pub = SqlMessageOutboxPublisher(session_factory, MESSAGE_DELIVERY_MODELS)
        await outbox_pub.publish([_ingestion_payload()])
        relay = MessageOutboxToInboxRelay(
            session_factory,
            models=MESSAGE_DELIVERY_MODELS,
            target_session_factory=target_session_factory,
            target_models=MESSAGE_DELIVERY_MODELS,
        )

        assert await relay.run_once() == 1
        assert await relay.run_once() == 0

        async with target_session_factory() as session:
            inbox_rows = (
                (await session.execute(select(MESSAGE_DELIVERY_MODELS.inbox))).scalars().all()
            )
        assert len(inbox_rows) == 1
