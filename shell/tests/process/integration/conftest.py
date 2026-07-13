"""Fixtures for process integration tests with SQLite."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from shell.platform.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.platform.infrastructure.persistence.memory import FakeClock, FakeEventPublisher
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.tests.shared.test_db import test_db_url

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    url = test_db_url(tmp_path_factory, subdir="sqlite", db_name="test_saga.db")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    return build_session_factory(url)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock(datetime(2024, 1, 1, tzinfo=UTC))


@pytest.fixture()
def sql_uow(
    session_factory: async_sessionmaker,
    events: FakeEventPublisher,
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)
