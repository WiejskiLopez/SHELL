from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.queries.queries import GetPromptQuery
from shell.application.query_handlers.query_handlers import GetPromptHandler
from shell.infrastructure.persistence.sql.services import PromptQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestPgUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        uow,
        clock,
        id_gen,
        session_factory,
    ) -> None:
        try:
            async with uow as u:
                from shell.domain.entities.prompt import Prompt
                from shell.domain.value_objects.ids import PromptId

                await u.prompts.save(
                    Prompt.new(
                        id_=PromptId("pg-rollback-prompt-x"),
                        name="pg-rollback-prompt-x",
                        body="should not persist",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced pg rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(PromptQueryService(session_factory))
        dto = await q.handle(GetPromptQuery("pg-rollback-prompt-x"))
        assert dto is None
