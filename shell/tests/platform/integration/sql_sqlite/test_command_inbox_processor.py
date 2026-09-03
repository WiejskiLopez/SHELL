"""SQLite integration tests for command inbox processing and retry policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import select

from shell.platform.application.commands.command import Command
from shell.platform.application.contracts.command_contract import CommandContract
from shell.platform.infrastructure.context import (
    DeliverySessionScope,
    reset_session_scope,
    set_session_scope,
)
from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.messaging.command.sql_command_outbox_writer import (
    SqlCommandOutboxWriter,
)
from shell.platform.infrastructure.messaging.command_transport import CommandOutboxToTransportRelay
from shell.tests.platform.integration.platform_delivery_models import (
    COMMAND_DELIVERY_MODELS,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.application.bus.command_bus import CommandBus

_INBOX_MODEL: Any = COMMAND_DELIVERY_MODELS.inbox


@dataclass(frozen=True, slots=True)
class SampleCommand(Command):
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
                command_id=f"cmd-{command_id}",
                command_name="SampleCommand",
                source_service="session",
                target_service="execution",
                schema_version=1,
                issued_at=datetime.now(tz=UTC),
                payload={"command_id": f"cmd-{command_id}"},
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
        writer = SqlCommandOutboxWriter(COMMAND_DELIVERY_MODELS, source_service="session")
        async with session_factory() as session:
            scope = DeliverySessionScope(session=session)
            token = set_session_scope(scope)
            try:
                writer.append(
                    session,
                    contract=CommandContract(
                        command_name="SampleCommand",
                        command_class=SampleCommand,
                        target_service="execution",
                        schema_version=1,
                    ),
                    payload={},
                    command_id="cmd-outbox-1",
                    issued_at=datetime.now(tz=UTC),
                )
            finally:
                reset_session_scope(token)
            await session.commit()
        transport = RecordingTransport()
        relay = CommandOutboxToTransportRelay(
            session_factory,
            models=COMMAND_DELIVERY_MODELS,
            transport=transport,
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
