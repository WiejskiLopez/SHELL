from __future__ import annotations

from shell.application.execution.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.platform.commands.commands import (
    ImportTaskExecutionCommand,
)
from shell.application.platform.queries.queries import (
    GetCurrentTaskExecutionQuery,
)
from shell.application.platform.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
)
from shell.infrastructure.execution.persistence.sql.services import TaskExecutionQueryService
from shell.infrastructure.platform.persistence.memory import FakeLogger


class TestPgTaskExecutionRepository:
    async def test_import_and_get_current(
        self,
        sql_uow,
        clock,
        id_gen,
        events,
        task_execution_loader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            sql_uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "pg-task"))

        q = GetCurrentTaskExecutionHandler(TaskExecutionQueryService(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("pg-task"))
        assert dto is not None
        assert dto.name == "pg-task"
        assert dto.is_current is True

    async def test_reimport_marks_old_non_current(
        self,
        sql_uow,
        clock,
        id_gen,
        events,
        task_execution_loader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            sql_uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "pg-task-v"))
        await handler.handle(ImportTaskExecutionCommand("t.md", "pg-task-v"))

        q = GetCurrentTaskExecutionHandler(TaskExecutionQueryService(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("pg-task-v"))
        assert dto is not None
        assert dto.is_current is True
