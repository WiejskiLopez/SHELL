"""Execution BC test fixtures — only what execution tests need."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from shell.execution.migrations.baseline import run_execution_baseline
from shell.platform.infrastructure.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
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
def unit_of_work() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture
def queries(unit_of_work: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(unit_of_work)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock(datetime(2024, 1, 1, tzinfo=UTC))


@pytest.fixture()
def id_generator() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    url = test_db_url(tmp_path_factory, subdir="sqlite", db_name="test.db")
    await run_execution_baseline(url)
    return build_session_factory(url)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


