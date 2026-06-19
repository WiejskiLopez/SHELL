from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeTaskLoader,
)
from shell.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await bootstrap_database(url)
    return build_session_factory(url)


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
    return FakeTaskLoader(md="# SQL Task")
