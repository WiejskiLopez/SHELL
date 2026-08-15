"""SQLite integration tests for command inbox processing and retry policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from shell.platform.infrastructure.messaging.command.command_outbox_to_inbox_relay import (
    CommandOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.messaging.command.sql_command_outbox_publisher import (
    SqlCommandOutboxPublisher,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.tests.platform.integration.platform_delivery_models import (
    COMMAND_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.application.bus.command_bus import CommandBus

_INBOX_MODEL: Any = COMMAND_DELIVERY_MODELS.inbox


@dataclass
class SampleCommand:
    value: str = "ok"


class FakeCommandBus:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.dispatched: list[object] = []

    async def dispatch(self, command: object) -> None:
        if self.fail:
            raise RuntimeError("dispatch failed")
        self.dispatched.append(command)


async def _create_command_table(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        connection = await session.connection()
        await connection.run_sync(COMMAND_DELIVERY_MODELS.inbox.metadata.create_all)


async def _add_command(session_factory: async_sessionmaker, command_id: str = "command-1") -> None:
    async with session_factory() as session:
        session.add(
            COMMAND_DELIVERY_MODELS.inbox(
                id=command_id,
                command_type="SampleCommand",
                occurred_at=datetime.now(tz=UTC),
                payload={},
                correlation_id="correlation",
                causation_id="causation",
                received_at=datetime.now(tz=UTC),
            )
        )
        await session.commit()


class TestCommandInboxProcessor:
    async def test_relay_can_write_to_a_separate_database(
        self,
        session_factory: async_sessionmaker,
        tmp_path,
    ) -> None:
        target_url = f"sqlite+aiosqlite:///{tmp_path / 'target-command.db'}"
        target_engine = create_async_engine(target_url)
        async with target_engine.begin() as connection:
            await connection.run_sync(COMMAND_DELIVERY_MODELS.inbox.metadata.create_all)
        await target_engine.dispose()
        target_session_factory = build_session_factory(target_url)

        publisher = SqlCommandOutboxPublisher(session_factory, COMMAND_DELIVERY_MODELS)
        await publisher.publish(
            command_type="SampleCommand",
            payload={},
            occurred_at=datetime.now(tz=UTC),
        )
        relay = CommandOutboxToInboxRelay(
            session_factory,
            models=COMMAND_DELIVERY_MODELS,
            target_session_factory=target_session_factory,
            target_models=COMMAND_DELIVERY_MODELS,
        )

        assert await relay.run_once() == 1
        assert await relay.run_once() == 0

        async with target_session_factory() as session:
            inbox_rows = (
                (await session.execute(select(COMMAND_DELIVERY_MODELS.inbox))).scalars().all()
            )
        assert len(inbox_rows) == 1

    async def test_success_marks_command_processed(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _create_command_table(session_factory)
        await _add_command(session_factory)
        bus = FakeCommandBus()

        processor = CommandInboxProcessor(
            session_factory,
            cast("CommandBus", bus),
            registry={"SampleCommand": SampleCommand},
            models=COMMAND_DELIVERY_MODELS,
        )
        result = await processor.run_once()
        assert result.claimed_count == 1
        assert result.processed_count == 1
        assert len(bus.dispatched) == 1

        async with session_factory() as session:
            row = (
                await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == "command-1"))
            ).scalar_one()
        assert row.processed_at is not None
        assert row.retry_count == 0

    async def test_failures_retry_then_move_to_dlq(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        await _create_command_table(session_factory)
        await _add_command(session_factory, command_id="command-2")
        processor = CommandInboxProcessor(
            session_factory,
            cast("CommandBus", FakeCommandBus(fail=True)),
            max_retries=2,
            retry_backoff_seconds=0,
            registry={"SampleCommand": SampleCommand},
            models=COMMAND_DELIVERY_MODELS,
        )

        first = await processor.run_once()
        assert first.retried_count == 1
        second = await processor.run_once()
        assert second.dead_lettered_count == 1

        async with session_factory() as session:
            row = (
                await session.execute(select(_INBOX_MODEL).where(_INBOX_MODEL.id == "command-2"))
            ).scalar_one()
        assert row.processed_at is None
        assert row.retry_count == 2
        assert row.error_code == "HANDLER_ERROR"
        assert row.failed_at is not None
