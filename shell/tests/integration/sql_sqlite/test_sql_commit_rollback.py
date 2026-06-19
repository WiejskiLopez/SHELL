"""SQLite integration tests — UnitOfWork commit/rollback behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.queries.queries import GetPromptQuery
from shell.application.query_handlers.query_handlers import GetPromptHandler
from shell.domain.entities.prompt import Prompt
from shell.domain.value_objects.ids import PromptId
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory.memory import FakeClock, FakeIdGenerator
from shell.infrastructure.persistence.sql.services import PromptQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlCommitRollback:
    async def test_rollback_on_exception(
        self,
        session_factory: async_sessionmaker,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        try:
            async with uow as u:
                await u.prompts.save(
                    Prompt.new(
                        id_=id_gen.new_prompt_id(),
                        name="rollback-prompt",
                        body="body",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(PromptQueryService(session_factory))
        dto = await q.handle(GetPromptQuery("rollback-prompt"))
        assert dto is None
