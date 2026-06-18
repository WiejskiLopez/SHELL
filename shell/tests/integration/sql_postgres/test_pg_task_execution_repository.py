from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.commands.commands import (
    ImportTaskExecutionCommand,
)
from shell.application.queries.queries import (
    GetCurrentTaskExecutionQuery,
)
from shell.application.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
)
from shell.infrastructure.persistence.memory.memory import FakeLogger
from shell.infrastructure.persistence.sql.query_services import SqlQueryServices

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestPgTaskExecutionRepository:
    async def test_import_and_get_current(
        self,
        uow,
        clock,
        id_gen,
        events,
        task_execution_loader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "pg-task"))

        q = GetCurrentTaskExecutionHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("pg-task"))
        assert dto is not None
        assert dto.name == "pg-task"
        assert dto.is_current is True

    async def test_reimport_marks_old_non_current(
        self,
        uow,
        clock,
        id_gen,
        events,
        task_execution_loader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "pg-task-v"))
        await handler.handle(ImportTaskExecutionCommand("t.md", "pg-task-v"))

        q = GetCurrentTaskExecutionHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("pg-task-v"))
        assert dto is not None
        assert dto.is_current is True
