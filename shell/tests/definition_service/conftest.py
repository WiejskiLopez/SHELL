"""Definition BC test fixtures — only what definition tests need."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from shell.definition_service.infrastructure.definition.persistence.memory.unit_of_work import (
    InMemoryDefinitionUnitOfWork,
)
from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.unit_of_work import (
    SqlAlchemyRunnerConfigUnitOfWork,
)
from shell.definition_service.migrations.baseline import run_definition_baseline
from shell.platform.infrastructure.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.tests.shared.test_db import build_db_url as test_db_url

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

POSTGRES_URL = os.environ.get(
    "POSTGRES_TEST_URL",
    "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test",
)

_postgres_available = os.environ.get("POSTGRES_TEST_URL") is not None

skip_no_postgres = pytest.mark.skipif(
    not _postgres_available,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)


@pytest.fixture(scope="session")
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    return test_db_url(tmp_path_factory, subdir="db", db_name="test.db")


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    return POSTGRES_URL


@pytest.fixture()
def unit_of_work() -> InMemoryDefinitionUnitOfWork:
    return InMemoryDefinitionUnitOfWork()


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    url = test_db_url(tmp_path_factory, subdir="sqlite", db_name="test.db")
    await run_definition_baseline(url)
    return build_session_factory(url)


@pytest.fixture()
def sql_uow(
    session_factory: async_sessionmaker,
) -> SqlAlchemyRunnerConfigUnitOfWork:
    return SqlAlchemyRunnerConfigUnitOfWork(session_factory, models=PERSISTENCE_DELIVERY_MODELS)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock(datetime(2024, 1, 1, tzinfo=UTC))


@pytest.fixture()
def id_generator() -> FakeIdGenerator:
    return FakeIdGenerator()
