"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.query_handlers.runner_config_get_handler import (
    RunnerConfigGetHandler as GetRunnerConfigHandler,
)
from shell.application.definition.queries.runner_config_get_query import RunnerConfigGetQuery as GetRunnerConfigQuery
from shell.infrastructure.definition.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService as SqlRunnerConfigQueryService,
)
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        session_factory: async_sessionmaker,
    ) -> None:
        try:
            async with sql_uow as u:
                from shell.domain.definition.entities.runner_config import RunnerConfig
                from shell.domain.definition.value_objects.ids import RunnerConfigId
                from shell.domain.platform.value_objects.hash import Hash

                await u.repository(RunnerConfigRepository).save(
                    RunnerConfig.new(
                        id_=RunnerConfigId("rollback-runner-x"),
                        package_name="rollback-runner-x",
                        kind="python",
                        body={"key": "value"},
                        config_hash=Hash.of("test"),
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigQuery("rollback-runner-x"))
        assert dto is None
