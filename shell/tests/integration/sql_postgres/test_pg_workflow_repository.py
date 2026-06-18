from __future__ import annotations

from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.commands.commands import (
    ImportTaskExecutionCommand,
    StartWorkflowCommand,
)
from shell.application.queries.queries import (
    GetWorkflowQuery,
)
from shell.application.query_handlers.query_handlers import (
    GetWorkflowHandler,
)
from shell.infrastructure.persistence.memory.memory import FakeLogger
from shell.infrastructure.persistence.sql.query_services import SqlQueryServices



class TestPgWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow,
        clock,
        id_gen,
        events,
        task_execution_loader,
        session_factory,
    ) -> None:
        imp = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())
        await imp.handle(ImportTaskExecutionCommand("t.md", "pg-wf-task"))

        from shell.domain.value_objects.task_execution_name import TaskExecutionName

        async with uow as u:
            task_execution = await u.task_executions.get_current_by_name(
                TaskExecutionName("pg-wf-task")
            )
            assert task_execution is not None
            real_task_execution_id = task_execution.id.value

        start = StartWorkflowHandler(uow, clock, id_gen)
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"

    async def test_workflow_not_found_returns_none(
        self,
        uow,
        session_factory,
    ) -> None:
        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery("pg-no-such-wf"))
        assert dto is None
