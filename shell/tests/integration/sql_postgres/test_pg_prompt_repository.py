from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.commands.commands import SavePromptCommand
from shell.application.queries.queries import GetPromptQuery
from shell.application.query_handlers.query_handlers import GetPromptHandler
from shell.infrastructure.persistence.sql.query_services import SqlQueryServices



class TestPgPromptRepository:
    async def test_save_and_get_prompt(
        self,
        uow,
        clock,
        id_gen,
        session_factory,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("pg-sys-prompt", "You are a pg helper."))

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("pg-sys-prompt"))
        assert dto is not None
        assert dto.body == "You are a pg helper."

    async def test_prompt_not_found_returns_none(
        self,
        uow,
        session_factory,
    ) -> None:
        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("pg-missing-prompt"))
        assert dto is None
