"""SQLite integration tests for command inbox processing and retry policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import select

from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.messaging.command.sql_command_outbox_publisher import (
    SqlCommandOutboxPublisher,
)
from shell.platform.infrastructure.messaging.transport import OutboxToTransportRelay
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


class RecordingTransport:
    def __init__(self) -> None:
        self.envelopes: list[object] = []

    async def deliver(self, envelope: object) -> None:
        self.envelopes.append(envelope)


async def _create_command_table(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        connection = await session.connection()
        await connection.run_sync(COMMAND_DELIVERY_MODELS.inbox.metadata.create_all)


async def _add_command(session_factory: async_sessionmaker, command_id: str = "command-1") -> None:
    async with session_factory() as session:
        session.add(
            COMMAND_DELIVERY_MODELS.inbox(
                id=command_id,
                outbox_id=f"outbox-{command_id}",
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
    async def test_shared_relay_delivers_command_to_transport(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        publisher = SqlCommandOutboxPublisher(session_factory, COMMAND_DELIVERY_MODELS)
        await publisher.publish(
            command_type="SampleCommand",
            payload={},
            occurred_at=datetime.now(tz=UTC),
        )
        transport = RecordingTransport()
        relay = OutboxToTransportRelay(
            session_factory,
            models=COMMAND_DELIVERY_MODELS,
            transport=transport,
            kind="command",
        )

        assert await relay.run_once() == 1
        assert await relay.run_once() == 0
        assert len(transport.envelopes) == 1

        async with session_factory() as session:
            rows = (await session.execute(select(COMMAND_DELIVERY_MODELS.outbox))).scalars().all()
        assert rows[0].published_at is not None

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
