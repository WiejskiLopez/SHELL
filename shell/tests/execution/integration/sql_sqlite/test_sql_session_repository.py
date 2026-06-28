"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.execution.persistence.sql.services import SessionQueryService
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
)
from shell.infrastructure.platform.persistence.memory import (  # noqa: TC002 — FakeClock, FakeIdGenerator używane w sygnaturach fixture'ów pytest
    FakeClock,
    FakeIdGenerator,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlSessionRepository:
    async def test_open_close_and_history(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.platform.commands import (
            CloseSessionCommand,
            OpenSessionCommand,
        )
        from shell.application.platform.queries.queries import SessionGetHistoryQuery
        from shell.application.platform.query_handlers import (
            SessionGetHistoryHandler,
        )
        from shell.application.session.command_handlers.session_handlers import (
            SessionCloseHandler,
            SessionOpenHandler,
        )

        session_id = await SessionOpenHandler(sql_uow, clock, id_generator).handle(
            OpenSessionCommand(goal="integration test")
        )
        await SessionCloseHandler(sql_uow, clock).handle(
            CloseSessionCommand(session_id=session_id.value)
        )

        dto = await SessionGetHistoryHandler(SessionQueryService(session_factory)).handle(
            SessionGetHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "closed"
