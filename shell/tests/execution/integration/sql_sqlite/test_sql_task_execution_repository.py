"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations
import pytest

from shell.application.execution.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.platform.commands.commands import ImportTaskExecutionCommand
from shell.application.platform.queries.queries import (
    GetCurrentTaskExecutionQuery,
)
from shell.application.platform.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
)
from shell.infrastructure.execution.persistence.sql.services import TaskExecutionQueryService
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)


class TestSqlTaskExecutionRepository:
    async def test_import_and_get_current(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            sql_uow, clock, id_generator, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task"))

        q = GetCurrentTaskExecutionHandler(TaskExecutionQueryService(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"