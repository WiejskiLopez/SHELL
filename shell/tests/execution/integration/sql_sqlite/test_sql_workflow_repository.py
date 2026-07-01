"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.persistence.sql.services import WorkflowQueryService
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence import (
        SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
    )


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
        imp = TaskExecutionImportHandler(
            sql_uow, clock, id_generator, task_execution_loader, FakeLogger()
        )
        await imp.handle(ImportTaskExecutionCommand("t.md", "wf-task"))

        async with sql_uow as u:
            task_execution = await u.repository(TaskExecutionRepository).get_current_by_name(  # type: ignore[type-abstract]
                TaskExecutionName("wf-task")
            )
            assert task_execution is not None
            real_task_execution_id = task_execution.id.value
            graph_execution = GraphExecution(
                id=GraphExecutionId.generate(),
                task_execution_id=task_execution.id,
                depth=GraphDepth(0),
                max_subgraph_depth=MaxSubgraphDepth(5),
            )
            node = GraphNodeExecution(
                id=GraphNodeExecutionId("wf-task-node-0"),
                position=NodeOrder(0),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),
            )
            node._graph_execution_id = graph_execution.id
            await u.repository(GraphExecutionRepository).save(graph_execution)  # type: ignore[type-abstract]
            await u.repository(GraphNodeExecutionRepository).save(node)  # type: ignore[type-abstract]
            await u.commit()

        start = WorkflowStartHandler(sql_uow, clock, id_generator)
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = WorkflowGetByIdHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(WorkflowGetByIdQuery(wf_id))
        assert dto is not None
        assert dto.status == "active"

    async def test_workflow_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = WorkflowGetByIdHandler(WorkflowQueryService(session_factory))
        dto = await q.handle(WorkflowGetByIdQuery("no-such-wf"))
        assert dto is None
