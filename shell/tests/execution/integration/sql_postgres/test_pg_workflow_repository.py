from __future__ import annotations

from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.command_handlers.workflow_start_handler import WorkflowStartHandler
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.commands.workflow_commands import StartWorkflowCommand
from shell.application.execution.queries.workflow_get_by_id_query import WorkflowGetByIdQuery
from shell.application.execution.query_handlers.workflow_get_by_id_handler import (
    WorkflowGetByIdHandler,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.value_objects.task_execution_name import (
    TaskExecutionName,
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

        async with sql_uow as u:
            task_execution = await u.repository(TaskExecutionRepository).get_current_by_name(
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
