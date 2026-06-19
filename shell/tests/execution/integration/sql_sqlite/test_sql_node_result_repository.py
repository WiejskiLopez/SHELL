"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.platform.commands.commands import (
    SaveGraphNodeExecutionResultCommand,
)
from shell.application.platform.queries.queries import (
    GetGraphNodeExecutionResultQuery,
)
from shell.application.platform.query_handlers.query_handlers import (
    GetGraphNodeExecutionResultHandler,
)
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator
)
from shell.infrastructure.execution.persistence.sql.services import NodeResultQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlNodeResultRepository:
    async def test_save_and_get_result(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.domain.execution.aggregates.workflow import Workflow
        from shell.domain.execution.value_objects.ids import WorkflowId

        async with sql_uow as u:
            await u.workflows.save(
                Workflow.new(
                    id_=WorkflowId("wf-sql-nr-1"),
                    now=clock.now(),
                )
            )

        handler = SaveGraphNodeExecutionResultHandler(sql_uow, clock, id_gen)
        await handler.handle(
            SaveGraphNodeExecutionResultCommand(
                workflow_id="wf-sql-nr-1",
                graph_node_execution_id="node-sql-nr-1",
                status="done",
                stdout="success",
            )
        )

        q = GetGraphNodeExecutionResultHandler(NodeResultQueryService(session_factory))
        dto = await q.handle(GetGraphNodeExecutionResultQuery("node-sql-nr-1", "wf-sql-nr-1"))
        assert dto is not None
        assert dto.stdout == "success"
        assert dto.status == "done"
