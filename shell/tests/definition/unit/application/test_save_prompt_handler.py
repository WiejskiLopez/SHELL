"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from shell.application.definition.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.platform.commands.commands import SavePromptCommand
from shell.application.platform.queries.queries import GetPromptQuery
from shell.application.platform.query_handlers.query_handlers import GetPromptHandler
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    InMemoryQueryServices,
    InMemoryUnitOfWork
)


class TestSavePromptHandler:
    async def test_happy_path(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("system", "You are a helpful assistant."))

        q_handler = GetPromptHandler(queries)
        dto = await q_handler.handle(GetPromptQuery("system"))
        assert dto is not None
        assert dto.body == "You are a helpful assistant."
        assert dto.is_current is True

    async def test_re_save_marks_old_non_current(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("system", "v1"))
        await handler.handle(SavePromptCommand("system", "v2"))

        q_handler = GetPromptHandler(queries)
        dto = await q_handler.handle(GetPromptQuery("system"))
        assert dto is not None
        assert dto.body == "v2"
