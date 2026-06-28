from __future__ import annotations

from shell.application.execution.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.execution.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.platform.commands import (
    ImportTaskExecutionCommand,
    StartWorkflowCommand,
)
from shell.application.platform.queries.queries import (
    GetWorkflowQuery,
)
from shell.application.platform.query_handlers import (
    GetWorkflowHandler,
)
from shell.infrastructure.execution.persistence.sql.services import WorkflowQueryService
from shell.infrastructure.platform.persistence.memory import FakeLogger


class TestPgWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        sql_uow,
        clock,
        id_gen,
        events,
        task_execution_loader,
        session_factory,
    ) -> None:
        imp = ImportTaskExecutionHandler(
            sql_uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await imp.handle(ImportTaskExecutionCommand("t.md", "pg-wf-task"))

        from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName

        async with sql_uow as u:
            task_execution = await u.task_execution_repository.get_current_by_name(
                TaskExecutionName("pg-wf-task")
            )
            assert task_execution is not None
            real_task_execution_id = task_execution.id.value

        start = StartWorkflowHandler(sql_uow, clock, id_gen)
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = GetWorkflowHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"

    async def test_workflow_not_found_returns_none(
        self,
        sql_uow,
        session_factory,
    ) -> None:
        q = GetWorkflowHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(GetWorkflowQuery("pg-no-such-wf"))
        assert dto is None
