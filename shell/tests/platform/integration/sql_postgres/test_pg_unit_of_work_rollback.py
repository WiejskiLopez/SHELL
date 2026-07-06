from __future__ import annotations

from shell.application.definition.runner_config.queries.runner_config_get_query import (
    RunnerConfigGetQuery as GetRunnerConfigQuery,
)
from shell.application.definition.runner_config.query_handlers.runner_config_get_handler import (
    RunnerConfigGetHandler as GetRunnerConfigHandler,
)
from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.definition.value_objects.package_name import PackageName
from shell.domain.definition.value_objects.runner_body import RunnerBody
from shell.domain.definition.value_objects.runner_kind import RunnerKind
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.hash import Hash
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
                        package_name=PackageName("pg-rollback-runner-x"),
                        kind=RunnerKind("python"),
                        body=RunnerBody({"key": "value"}),
                        config_hash=Hash.of("test"),
                        now=CreatedAt.from_datetime(clock.now()),
                    )
                )
                raise RuntimeError("forced pg rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigQuery("pg-rollback-runner-x"))
        assert dto is None
