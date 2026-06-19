"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.platform.logging.stdlib_logger import get_correlation_id
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator
)
from shell.infrastructure.execution.persistence.sql.services import SessionQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlSessionRepository:
    async def test_open_append_close_and_history(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.execution.command_handlers.session_handlers import (
            AppendMessageHandler,
            CloseSessionHandler,
            OpenSessionHandler,
        )
        from shell.application.platform.commands.commands import (
            AppendMessageCommand,
            CloseSessionCommand,
            OpenSessionCommand,
        )
        from shell.application.platform.queries.queries import GetSessionHistoryQuery
        from shell.application.platform.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="integration test")
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(
                session_id=session_id.value,
                correlation_id=get_correlation_id(),
                sender="sql-agent",
                receiver="router",
                payload={"k": 1},
            )
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(
                session_id=session_id.value,
                correlation_id=get_correlation_id(),
                sender="router",
                receiver="sql-agent",
                payload={"k": 2},
            )
        )
        await CloseSessionHandler(uow, clock).handle(
            CloseSessionCommand(session_id=session_id.value)
        )

        dto = await GetSessionHistoryHandler(SessionQueryService(session_factory)).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "closed"
        assert len(dto.messages) == 2
