"""Integration fixtures for platform persistence and messaging tests."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.unit_of_work import (
    SqlAlchemyRunnerConfigUnitOfWork,
)
from shell.definition_service.migrations.baseline import run_definition_baseline
from shell.platform.infrastructure.persistence.memory import FakeEventPublisher
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.tests.shared.test_db import build_db_url as test_db_url

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

POSTGRES_URL = os.environ.get(
    "POSTGRES_TEST_URL",
    "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test",
)
MONGO_URL = os.environ.get("MONGO_TEST_URL", "mongodb://localhost:27018/?replicaSet=rs0")

_postgres_available = os.environ.get("POSTGRES_TEST_URL") is not None
_mongo_available = os.environ.get("MONGO_TEST_URL") is not None

skip_no_postgres = pytest.mark.skipif(
    not _postgres_available,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)

skip_no_mongo = pytest.mark.skipif(
    not _mongo_available,
    reason="MONGO_TEST_URL not set — start docker-compose.test.yml to enable",
)


@pytest.fixture(scope="session")
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    return test_db_url(tmp_path_factory, subdir="db", db_name="test.db")


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    return POSTGRES_URL


@pytest.fixture(scope="session")
def mongo_test_url() -> str:
    return MONGO_URL


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    url = test_db_url(tmp_path_factory, subdir="sqlite", db_name="test.db")
    await run_definition_baseline(url)
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
    await engine.dispose()
    return build_session_factory(url)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def sql_uow(
    session_factory: async_sessionmaker,
    events: FakeEventPublisher,
) -> SqlAlchemyRunnerConfigUnitOfWork:
    return SqlAlchemyRunnerConfigUnitOfWork(session_factory, models=PERSISTENCE_DELIVERY_MODELS)


@pytest.fixture(scope="function")
async def pg_session_factory() -> async_sessionmaker:
    """PostgreSQL-backed session factory (requires POSTGRES_TEST_URL).

    Function-scoped so each test owns its event loop (avoids Windows proactor
    "attached to a different loop" issues across function-scoped pytest-asyncio
    loops).
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(POSTGRES_URL)
    async with engine.begin() as connection:
        await connection.run_sync(EVENT_DELIVERY_MODELS.outbox.metadata.create_all)
    await engine.dispose()
    return build_session_factory(POSTGRES_URL)
