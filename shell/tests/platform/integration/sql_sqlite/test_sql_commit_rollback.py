"""SQLite integration tests — UnitOfWork commit/rollback behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition.application.definition.runner_config.queries.get_runner_config_by_id_query import (
    GetRunnerConfigByIdQuery,
)
from shell.definition.application.definition.runner_config.query_handlers.get_runner_config_by_id_handler import (
    GetRunnerConfigByIdHandler,
)
from shell.definition.domain.definition.aggregates.runner_config.repositories.runner_config_repository import (
    RunnerConfigRepository,
)
from shell.definition.domain.definition.aggregates.runner_config.runner_config import RunnerConfig
from shell.definition.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.definition.infrastructure.definition.runner_config.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService as SqlRunnerConfigQueryService,
)
from shell.definition.infrastructure.definition.runner_config.persistence.sql.unit_of_work import (
    SqlAlchemyRunnerConfigUnitOfWork,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.infrastructure.persistence.memory import FakeClock, FakeIdGenerator


class TestSqlCommitRollback:
    async def test_rollback_on_exception(
        self,
        session_factory: async_sessionmaker,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        sql_uow = SqlAlchemyRunnerConfigUnitOfWork(session_factory)
        try:
            async with sql_uow as u:
                await u.repository(RunnerConfigRepository).save(  # type: ignore[type-abstract]
                    RunnerConfig.create(
                        id_=id_generator.new_id(RunnerConfigId),
                        now=CreatedAt.from_datetime(clock.now()),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigByIdHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigByIdQuery("rollback-runner"))
        assert dto is None
