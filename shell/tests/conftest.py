"""Root conftest for shell tests.

Provides fixtures for all three persistence backends:
- InMemory (always available)
- SQLite (always available)
- PostgreSQL (skipped unless POSTGRES_TEST_URL env var set)
- MongoDB (skipped unless MONGO_TEST_URL env var set)
"""

from __future__ import annotations

import uuid

import pytest
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)
from shell.infrastructure.platform.logging.stdlib_logger import correlation_id_var
from shell.tests.conftest_helpers import *

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: integration tests requiring external services")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


# ---------------------------------------------------------------------------
# Backend availability flags
# ---------------------------------------------------------------------------

import os

POSTGRES_URL = os.environ.get(
    "POSTGRES_TEST_URL",
    "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test",
)
MONGO_URL = os.environ.get("MONGO_TEST_URL", "mongodb://localhost:27018/?replicaSet=rs0")

_postgres_available = os.environ.get("POSTGRES_TEST_URL") is not None
_mongo_available = os.environ.get("MONGO_TEST_URL") is not None

# ---------------------------------------------------------------------------
# Skip helpers
# ---------------------------------------------------------------------------

skip_no_postgres = pytest.mark.skipif(
    not _postgres_available,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)

skip_no_mongo = pytest.mark.skipif(
    not _mongo_available,
    reason="MONGO_TEST_URL not set — start docker-compose.test.yml to enable",
)


# ---------------------------------------------------------------------------
# URL fixtures (for integration tests that need raw URLs)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    return POSTGRES_URL


@pytest.fixture(scope="session")
def mongo_test_url() -> str:
    return MONGO_URL


@pytest.fixture(autouse=True)
def auto_correlation_id():
    """Automatycznie ustawia correlation_id dla każdego testu."""
    token = correlation_id_var.set(f"test-{uuid.uuid4()}")
    yield
    correlation_id_var.reset(token)


@pytest.fixture
def queries(unit_of_work: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(unit_of_work)


@pytest.fixture()
def unit_of_work() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_generator() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def task_execution_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# SQL Task")


@pytest.fixture()
def fake_logger() -> FakeLogger:
    return FakeLogger()


# ---------------------------------------------------------------------------
# SQLite integration fixtures
# ---------------------------------------------------------------------------

import pathlib
from typing import TYPE_CHECKING

from shell.bootstrap.platform.database_config.database_bootstrap import bootstrap_database
from shell.infrastructure.platform.configuration.shell_config import ShellConfig
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.platform.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await bootstrap_database(ShellConfig(database_url=url))
    return build_session_factory(url)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def sql_uow(
    session_factory: async_sessionmaker,
    events: FakeEventPublisher,
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)


# ---------------------------------------------------------------------------
# PostgreSQL integration fixtures
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(config, items):
    if os.environ.get("PG_TEST_URL") is None:
        skip_pg = pytest.mark.skip(reason="PG_TEST_URL not set")
        for item in items:
            if "sql_postgres" in str(item.fspath):
                item.add_marker(skip_pg)
