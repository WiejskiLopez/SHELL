"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.platform.commands.commands import SavePromptCommand
from shell.application.platform.queries.queries import GetPromptQuery
from shell.application.platform.query_handlers.query_handlers import GetPromptHandler
from shell.infrastructure.definition.persistence.sql.services import PromptQueryService
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.platform.persistence.memory import FakeClock, FakeIdGenerator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlPromptRepository:
    async def test_save_and_get_prompt(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = SavePromptHandler(sql_uow, clock, id_gen)
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(PromptQueryService(session_factory))
        dto = await q.handle(GetPromptQuery("sys-prompt"))
        assert dto is not None
        assert dto.body == "You are helpful."

    async def test_prompt_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetPromptHandler(PromptQueryService(session_factory))
        dto = await q.handle(GetPromptQuery("missing-prompt"))
        assert dto is None
