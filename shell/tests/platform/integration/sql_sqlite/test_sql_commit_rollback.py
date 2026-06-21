"""SQLite integration tests — UnitOfWork commit/rollback behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.queries.queries import GetPromptQuery
from shell.application.platform.query_handlers.query_handlers import GetPromptHandler
from shell.domain.definition.entities.prompt import Prompt
from shell.infrastructure.definition.persistence.sql.services import PromptQueryService
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
)
from shell.infrastructure.platform.persistence.memory import (  # noqa: TC002 — FakeClock, FakeIdGenerator używane w sygnaturach fixture'ów pytest
    FakeClock,
    FakeIdGenerator,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlCommitRollback:
    async def test_rollback_on_exception(
        self,
        session_factory: async_sessionmaker,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        sql_uow = SqlAlchemyUnitOfWork(session_factory)
        try:
            async with sql_uow as u:
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
