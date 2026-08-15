from __future__ import annotations

import os
from typing import Any, cast

import pytest

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
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.tests.platform.integration.conftest import POSTGRES_URL

skip_no_postgres = pytest.mark.skipif(
    os.environ.get("POSTGRES_TEST_URL") is None,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)


@skip_no_postgres
class TestPgUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        clock,
        id_generator,
    ) -> None:
        from sqlalchemy.ext.asyncio import create_async_engine

        from shell.definition.infrastructure.definition.persistence.sql.models.base import (
            PERSISTENCE_DELIVERY_MODELS,
        )
        from shell.definition.infrastructure.definition.runner_config.persistence.sql.unit_of_work import (
            SqlAlchemyRunnerConfigUnitOfWork,
        )

        engine = create_async_engine(POSTGRES_URL)
        async with engine.begin() as connection:
            await connection.run_sync(PERSISTENCE_DELIVERY_MODELS.audit.metadata.create_all)
        await engine.dispose()
        session_factory = build_session_factory(POSTGRES_URL)

        sql_uow = SqlAlchemyRunnerConfigUnitOfWork(
            session_factory, models=PERSISTENCE_DELIVERY_MODELS
        )
        try:
            async with sql_uow as u:
                await u.repository(cast("type[Any]", RunnerConfigRepository)).save(
                    RunnerConfig.create(
                        id_=id_generator.new_id(RunnerConfigId),
                        now=CreatedAt.from_datetime(clock.now()),
                    )
                )
                raise RuntimeError("forced pg rollback")
        except RuntimeError:
            pass

        q = GetRunnerConfigByIdHandler(SqlRunnerConfigQueryService(session_factory))
        dto = await q.handle(GetRunnerConfigByIdQuery("pg-rollback-runner-x"))
        assert dto is None
