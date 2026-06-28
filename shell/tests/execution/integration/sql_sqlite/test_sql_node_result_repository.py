"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations
import pytest

from typing import TYPE_CHECKING

from shell.application.execution.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.platform.commands import (
    SaveGraphNodeExecutionResultCommand,
)
from shell.application.platform.queries.queries import (
    GetGraphNodeExecutionResultQuery,
)
from shell.application.platform.query_handlers import (
    GetGraphNodeExecutionResultHandler,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.persistence.sql.services import NodeResultQueryService
from shell.infrastructure.platform.persistence import (
    SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeEventPublisher,  # noqa: TC002 — FakeEventPublisher używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlNodeResultRepository:
    async def test_save_and_get_result(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        events: FakeEventPublisher,
        session_factory: async_sessionmaker,
    ) -> None:
        async with sql_uow as u:
            await u.workflow_repository.save(
                Workflow.new(
                    id_=WorkflowId("wf-sql-nr-1"),
                    now=clock.now(),
                )
            )
            node = GraphNodeExecution(
                id=GraphNodeExecutionId("node-sql-nr-1"),
                position=NodeOrder(0),
                mode=Mode.WORKER,
                role="worker",
                node_type=NodeType("worker"),
            )
            await u.graph_node_execution_repository.save(node)

        handler = SaveGraphNodeExecutionResultHandler(sql_uow, clock, id_generator)
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
