from __future__ import annotations

from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.command_handlers.workflow_start_handler import WorkflowStartHandler
from shell.application.platform.commands import (
    ImportTaskExecutionCommand,
    StartWorkflowCommand,
)
from shell.application.platform.queries.queries import (
    WorkflowGetByIdQuery,
)
from shell.application.platform.query_handlers import (
    WorkflowGetByIdHandler,
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
        imp = TaskExecutionImportHandler(
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

        start = WorkflowStartHandler(sql_uow, clock, id_gen)
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = WorkflowGetByIdHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(WorkflowGetByIdQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"

    async def test_workflow_not_found_returns_none(
        self,
        sql_uow,
        session_factory,
    ) -> None:
        q = WorkflowGetByIdHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(WorkflowGetByIdQuery("pg-no-such-wf"))
        assert dto is None
