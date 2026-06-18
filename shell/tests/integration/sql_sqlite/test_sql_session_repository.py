"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.logging.stdlib_logger import get_correlation_id
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
)
from shell.infrastructure.persistence.sql.services import SessionQueryService

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
        from shell.application.command_handlers.session_handlers import (
            AppendMessageHandler,
            CloseSessionHandler,
            OpenSessionHandler,
        )
        from shell.application.commands.commands import (
            AppendMessageCommand,
            CloseSessionCommand,
            OpenSessionCommand,
        )
        from shell.application.queries.queries import GetSessionHistoryQuery
        from shell.application.query_handlers.query_handlers import GetSessionHistoryHandler

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
