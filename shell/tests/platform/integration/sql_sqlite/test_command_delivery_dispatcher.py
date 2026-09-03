"""SQLite integration tests for build_command_delivery_dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.application.commands.command import Command
from shell.platform.application.contracts.command_contract import CommandContract
from shell.platform.infrastructure.context import (
    DeliverySessionScope,
    reset_session_scope,
    set_session_scope,
)
from shell.platform.infrastructure.process.saga.command_delivery import (
    build_command_delivery_dispatcher,
)
from shell.tests.platform.integration.platform_delivery_models import COMMAND_DELIVERY_MODELS

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


@dataclass(frozen=True, slots=True)
class SampleProcessCommand(Command):
    order_id: str = "order-1"


_CONTRACTS: dict[str, CommandContract] = {
    "sample_process_command": CommandContract(
        command_name="sample_process_command",
        command_class=SampleProcessCommand,
        target_service="execution",
        schema_version=1,
    )
}


async def _create_command_table(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        connection = await session.connection()
        await connection.run_sync(COMMAND_DELIVERY_MODELS.inbox.metadata.create_all)


class TestBuildCommandDeliveryDispatcher:
    async def test_dispatch_appends_outbox_row(self, session_factory: async_sessionmaker) -> None:
        await _create_command_table(session_factory)
        dispatcher = build_command_delivery_dispatcher(
            commands=_CONTRACTS,
            models=COMMAND_DELIVERY_MODELS,
            source_service="session",
        )

        async with session_factory() as session:
            scope = DeliverySessionScope(session=session)
            token = set_session_scope(scope)
            try:
                command_id = await dispatcher.dispatch(
                    SampleProcessCommand(), target_service="execution"
                )
            finally:
                reset_session_scope(token)
            await session.commit()

        assert command_id
        async with session_factory() as session:
            rows = (await session.execute(select(COMMAND_DELIVERY_MODELS.outbox))).scalars().all()
        assert len(rows) == 1
        assert rows[0].command_name == "sample_process_command"
        assert rows[0].target_service == "execution"
        assert rows[0].command_id == command_id
        assert rows[0].correlation_id

    async def test_dispatch_unknown_command_raises(
        self, session_factory: async_sessionmaker
    ) -> None:
        await _create_command_table(session_factory)

        @dataclass(frozen=True, slots=True)
        class UnknownCommand(Command):
            pass

        dispatcher = build_command_delivery_dispatcher(
            commands=_CONTRACTS,
            models=COMMAND_DELIVERY_MODELS,
            source_service="session",
        )
        async with session_factory() as session:
            scope = DeliverySessionScope(session=session)
            token = set_session_scope(scope)
            try:
                try:
                    await dispatcher.dispatch(UnknownCommand(), target_service="execution")
                except ValueError:
                    pass
                else:
                    raise AssertionError("brak kontraktu powinien rzucić ValueError")
            finally:
                reset_session_scope(token)
