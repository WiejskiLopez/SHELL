"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.execution.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.platform.commands.commands import (
    ImportTaskExecutionCommand,
    StartWorkflowCommand,
)
from shell.application.platform.queries.queries import GetWorkflowQuery
from shell.application.platform.query_handlers.query_handlers import GetWorkflowHandler
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader
)
from shell.infrastructure.execution.persistence.sql.services import WorkflowQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        imp = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())
        await imp.handle(ImportTaskExecutionCommand("t.md", "wf-task"))

        from shell.domain.execution.aggregates.graph_execution import GraphExecution, GraphNodeExecution
        from shell.domain.platform.value_objects.ids import (
            GraphDefinitionId,
            GraphExecutionId,
            GraphNodeExecutionId,
        )
        from shell.domain.platform.value_objects.mode import Mode
        from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName

        async with uow as u:
            task_execution = await u.task_executions.get_current_by_name(
                TaskExecutionName("wf-task")
            )
            assert task_execution is not None
            real_task_execution_id = task_execution.id.value
            graph_execution = GraphExecution(
                id=GraphExecutionId.generate(),
                task_execution_id=task_execution.id,
                graph_definition_id=GraphDefinitionId("tpl"),
                graph_node_executions=[
                    GraphNodeExecution(
                        id=GraphNodeExecutionId("wf-task-node-0"),
                        position=0,
                        mode=Mode("agent"),
                        role="agent",
                        node_type="agent",
                    )
                ],
            )
            await u.graph_executions.save(graph_execution)
            await u.commit()

        start = StartWorkflowHandler(uow, clock, id_gen)
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = GetWorkflowHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        assert dto.task_execution_id == real_task_execution_id

    async def test_workflow_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetWorkflowHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(GetWorkflowQuery("no-such-wf"))
        assert dto is None
