"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.queries.runner_config_get_query import (
    RunnerConfigGetQuery as GetRunnerConfigQuery,
)
from shell.application.definition.query_handlers.runner_config_get_handler import (
    RunnerConfigGetHandler as GetRunnerConfigHandler,
)
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.infrastructure.definition.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService as SqlRunnerConfigQueryService,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence import (
        SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
    )
    from shell.infrastructure.platform.persistence.memory import (
        FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    )


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
                        package_name=PackageName("rollback-runner-x"),
                        kind=RunnerKind("python"),
                        body=RunnerBody({"key": "value"}),
                        config_hash=Hash.of("test"),
                        now=CreatedAt.from_datetime(clock.now()),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigQuery("rollback-runner-x"))
        assert dto is None
