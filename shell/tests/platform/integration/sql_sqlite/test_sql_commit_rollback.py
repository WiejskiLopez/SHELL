"""SQLite integration tests — UnitOfWork commit/rollback behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.queries.queries import GetRunnerConfigQuery
from shell.application.platform.query_handlers.query_handlers import GetRunnerConfigHandler
from shell.infrastructure.definition.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService as SqlRunnerConfigQueryService,
)
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
                from shell.domain.definition.entities.runner_config import RunnerConfig
                from shell.domain.platform.value_objects.hash import Hash

                await u.runner_config_repository.save(
                    RunnerConfig.new(
                        id_=id_gen.new_runner_config_id(),
                        package_name="rollback-runner",
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
        dto = await q.handle(GetRunnerConfigQuery("rollback-runner"))
        assert dto is None
