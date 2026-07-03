"""SQLite integration tests — UnitOfWork commit/rollback behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.queries.runner_config_get_query import (
    RunnerConfigGetQuery as GetRunnerConfigQuery,
)
from shell.application.definition.query_handlers.runner_config_get_handler import (
    RunnerConfigGetHandler as GetRunnerConfigHandler,
)
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.infrastructure.definition.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService as SqlRunnerConfigQueryService,
)
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence.memory import (  # noqa: TC002 — FakeClock, FakeIdGenerator używane w sygnaturach fixture'ów pytest
        FakeClock,
        FakeIdGenerator,
    )


class TestSqlCommitRollback:
    async def test_rollback_on_exception(
        self,
        session_factory: async_sessionmaker,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        sql_uow = SqlAlchemyUnitOfWork(session_factory)  # type: ignore[abstract]
        try:
            async with sql_uow as u:
                await u.repository(RunnerConfigRepository).save(  # type: ignore[type-abstract]
                    RunnerConfig.new(
                        id_=id_generator.new_id(RunnerConfigId),
                        package_name=PackageName("rollback-runner"),
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
        dto = await q.handle(GetRunnerConfigQuery("rollback-runner"))
        assert dto is None
