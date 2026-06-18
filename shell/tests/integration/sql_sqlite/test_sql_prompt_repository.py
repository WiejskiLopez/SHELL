"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.commands.commands import SavePromptCommand
from shell.application.queries.queries import GetPromptQuery
from shell.application.query_handlers.query_handlers import GetPromptHandler
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
)
from shell.infrastructure.persistence.sql.query_services import SqlQueryServices

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlPromptRepository:
    async def test_save_and_get_prompt(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("sys-prompt"))
        assert dto is not None
        assert dto.body == "You are helpful."

    async def test_prompt_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("missing-prompt"))
        assert dto is None
