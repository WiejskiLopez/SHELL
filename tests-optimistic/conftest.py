"""Conftest for optimistic locking integration tests — standalone, no parent conftest dependency."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.execution_service.infrastructure.execution.workflow.persistence.sql.unit_of_work import (
    SqlAlchemyWorkflowUnitOfWork,
)
from shell.execution_service.migrations.baseline import run_execution_baseline
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await run_execution_baseline(url)
    return build_session_factory(url)


@pytest.fixture()
def sql_uow(
    session_factory: async_sessionmaker,
) -> SqlAlchemyWorkflowUnitOfWork:
    return SqlAlchemyWorkflowUnitOfWork(session_factory)
