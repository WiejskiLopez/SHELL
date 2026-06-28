"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.platform.commands import ImportTaskExecutionCommand
from shell.application.platform.queries.queries import (
    TaskExecutionGetCurrentQuery,
)
from shell.application.platform.query_handlers import (
    TaskExecutionGetCurrentHandler,
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
        handler = TaskExecutionImportHandler(
            sql_uow, clock, id_generator, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task"))

        q = TaskExecutionGetCurrentHandler(TaskExecutionQueryService(session_factory))
        dto = await q.handle(TaskExecutionGetCurrentQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"
