from __future__ import annotations

from shell.application.platform.queries.queries import GetRunnerConfigQuery
from shell.application.platform.query_handlers.query_handlers import GetRunnerConfigHandler
from shell.infrastructure.definition.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService as SqlRunnerConfigQueryService,
)


class TestPgUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        sql_uow,
        clock,
        id_gen,
        session_factory,
    ) -> None:
        try:
            async with sql_uow as u:
                from shell.domain.definition.entities.runner_config import RunnerConfig
                from shell.domain.platform.value_objects.hash import Hash

                await u.runner_configs.save(
                    RunnerConfig.new(
                        id_=id_gen.new_runner_config_id(),
                        package_name="pg-rollback-runner-x",
                        kind="python",
                        body={"key": "value"},
                        config_hash=Hash.of("test"),
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced pg rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigQuery("pg-rollback-runner-x"))
        assert dto is None
