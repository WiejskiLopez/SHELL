from __future__ import annotations

from shell.application.platform.queries.queries import GetPromptQuery
from shell.application.platform.query_handlers.query_handlers import GetPromptHandler
from shell.infrastructure.definition.persistence.sql.services import PromptQueryService

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
                from shell.domain.definition.entities.prompt import Prompt
                from shell.domain.platform.value_objects.ids import PromptId

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
