"""PostgreSQL integration tests — mirrors sql_sqlite tests on a real Postgres instance.

Skip all tests when PG_TEST_URL is not set:
    export PG_TEST_URL=postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test

Start Postgres via docker-compose:
    docker compose -f shell/docker-compose.test.yml up -d postgres
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from shell.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeTaskLoader,
)
from shell.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_PG_URL = os.environ.get(
    "PG_TEST_URL", "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test"
)

_DIR = os.path.dirname(os.path.abspath(__file__))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("PG_TEST_URL") is None:
        skip_pg = pytest.mark.skip(
            reason="PG_TEST_URL not set — start Postgres via docker-compose and set PG_TEST_URL"
        )
        for item in items:
            if str(item.fspath).startswith(_DIR):
                item.add_marker(skip_pg)


@pytest.fixture(scope="module")
async def session_factory() -> async_sessionmaker:
    await bootstrap_database(_PG_URL)
    return build_session_factory(_PG_URL)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def uow(
    session_factory: async_sessionmaker,
    events: FakeEventPublisher,
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def task_execution_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# PG Task")
