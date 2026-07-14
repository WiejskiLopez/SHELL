"""Conftest for optimistic locking integration tests — standalone, no parent conftest dependency."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.platform.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.platform.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.platform.infrastructure.persistence.sql import build_session_factory

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
def sql_uow(
    session_factory: async_sessionmaker,
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)
