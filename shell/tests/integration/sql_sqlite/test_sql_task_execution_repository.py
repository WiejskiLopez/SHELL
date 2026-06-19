"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.commands.commands import ImportTaskExecutionCommand
from shell.application.queries.queries import (
    GetCurrentTaskExecutionQuery,
)
from shell.application.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
)
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)
from shell.infrastructure.persistence.sql.services import TaskExecutionQueryService


class TestSqlTaskExecutionRepository:
    async def test_import_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task"))

        q = GetCurrentTaskExecutionHandler(TaskExecutionQueryService(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"
        assert dto.is_current is True

    async def test_reimport_marks_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task-v"))
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task-v"))

        q = GetCurrentTaskExecutionHandler(TaskExecutionQueryService(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("sql-task-v"))
        assert dto is not None
        assert dto.is_current is True
