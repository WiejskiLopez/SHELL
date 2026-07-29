"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.session.session.persistence.sql.services.session_query_service import (
    SessionQueryService,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.infrastructure.persistence import (
        SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
    )
    from shell.platform.infrastructure.persistence.memory import (  # noqa: TC002 — FakeClock, FakeIdGenerator używane w sygnaturach fixture'ów pytest
        FakeClock,
        FakeIdGenerator,
    )


from shell.application.session.session.command_handlers.close_session_handler import (
    CloseSessionHandler,
)
from shell.application.session.session.command_handlers.open_session_handler import (
    OpenSessionHandler,
)
from shell.application.session.session.commands import (
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell.application.session.session.queries.get_session_history_query import (
    GetSessionHistoryQuery,
)
from shell.application.session.session.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)


class TestSqlSessionRepository:
    async def test_open_close_and_history(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        session_id = await OpenSessionHandler(sql_uow, clock, id_generator).handle(
            OpenSessionCommand(goal="integration test")
        )
        await CloseSessionHandler(sql_uow, clock).handle(
            CloseSessionCommand(session_id=session_id.value)
        )

        dto = await GetSessionHistoryHandler(SessionQueryService(session_factory)).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "closed"
