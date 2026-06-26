"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations
import pytest

from typing import TYPE_CHECKING

from shell.application.execution.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.execution.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.platform.commands.commands import (
    ImportTaskExecutionCommand,
    StartWorkflowCommand,
)
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.mode import Mode
from shell.application.platform.queries.queries import GetWorkflowQuery
from shell.application.platform.query_handlers.query_handlers import GetWorkflowHandler
from shell.infrastructure.execution.persistence.sql.services import WorkflowQueryService
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        imp = ImportTaskExecutionHandler(
            sql_uow, clock, id_generator, task_execution_loader, FakeLogger()
        )
        await imp.handle(ImportTaskExecutionCommand("t.md", "wf-task"))

        async with sql_uow as u:
            task_execution = await u.task_execution_repository.get_current_by_name(
                TaskExecutionName("wf-task")
            )
            assert task_execution is not None
            real_task_execution_id = task_execution.id.value
            graph_execution = GraphExecution(
                id=GraphExecutionId.generate(),
                task_execution_id=task_execution.id,
            )
            node = GraphNodeExecution(
                id=GraphNodeExecutionId("wf-task-node-0"),
                position=NodeOrder(0),
                mode=Mode("agent"),
                role="agent",
                node_type=NodeType("agent"),
            )
            node._graph_execution_id = graph_execution.id
            await u.graph_execution_repository.save(graph_execution)
            await u.graph_node_execution_repository.save(node)
            await u.commit()

        start = StartWorkflowHandler(sql_uow, clock, id_generator)
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = GetWorkflowHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "active"

    async def test_workflow_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetWorkflowHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(GetWorkflowQuery("no-such-wf"))
        assert dto is None