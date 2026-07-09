from __future__ import annotations

from shell.application.definition.runner_config.queries.get_runner_config_by_id_query import (
    GetRunnerConfigByIdQuery,
)
from shell.application.definition.runner_config.query_handlers.get_runner_config_by_id_handler import (
    GetRunnerConfigByIdHandler,
)
from shell.domain.definition.aggregates.runner_config.repositories.runner_config_repository import (
    RunnerConfigRepository,
)
from shell.domain.definition.aggregates.runner_config.runner_config import RunnerConfig
from shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.infrastructure.definition.runner_config.persistence.sql.services.runner_config_query_service import (
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
                await u.repository(RunnerConfigRepository).save(
                    RunnerConfig.new(
                        id_=id_gen.new_id(RunnerConfigId),
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced pg rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigByIdHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigByIdQuery("pg-rollback-runner-x"))
        assert dto is None
