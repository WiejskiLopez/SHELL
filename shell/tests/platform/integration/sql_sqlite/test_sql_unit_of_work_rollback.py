"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,  # noqa: TC001 -- used at runtime for instantiation
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence.memory import FakeClock


class TestSqlUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        session_factory: async_sessionmaker,
    ) -> None:
        try:
            async with sql_uow as u:
                await u.repository(RunnerConfigRepository).save(  # type: ignore[type-abstract]
                    RunnerConfig.new(
                        id_=RunnerConfigId("rollback-runner-x"),
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigByIdHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigByIdQuery("rollback-runner-x"))
        assert dto is None
