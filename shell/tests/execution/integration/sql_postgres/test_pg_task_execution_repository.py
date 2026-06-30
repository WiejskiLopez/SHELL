from __future__ import annotations

from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.queries.task_execution_queries import TaskExecutionGetCurrentQuery
from shell.application.execution.query_handlers.task_execution_get_current_handler import (
    TaskExecutionGetCurrentHandler,
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
        handler = TaskExecutionImportHandler(
            sql_uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "pg-task"))

        q = TaskExecutionGetCurrentHandler(TaskExecutionQueryService(session_factory))
        dto = await q.handle(TaskExecutionGetCurrentQuery("pg-task"))
        assert dto is not None
        assert dto.name == "pg-task"
