"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.command_handlers.node_execution_save_result_handler import (
    NodeExecutionSaveResultHandler,
)
from shell.application.execution.commands.node_execution_commands import (
    SaveNodeExecutionResultCommand,
)
from shell.application.execution.queries.node_execution_get_result_query import (
    NodeExecutionGetResultQuery,
)
from shell.application.execution.query_handlers.node_execution_get_result_handler import (
    NodeExecutionGetResultHandler,
)
from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.value_objects.ids import NodeExecutionId, WorkflowId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.persistence.sql.services import NodeResultQueryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence import (
        SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
    )
    from shell.infrastructure.platform.persistence.memory import (
        FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
        FakeEventPublisher,  # noqa: TC002 — FakeEventPublisher używany w sygnaturach fixture'ów pytest
        FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    )


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
            await u.repository(WorkflowRepository).save(  # type: ignore[type-abstract]
                Workflow.new(
                    id_=WorkflowId("wf-sql-nr-1"),
                    now=clock.now(),
                )
            )
            node = NodeExecution(
                id=NodeExecutionId("node-sql-nr-1"),
                position=NodeOrder(0),
                mode=Mode.WORKER,
                role=NodeRole.AGENT,
                node_type=NodeType("worker"),
            )
            await u.repository(NodeExecutionRepository).save(node)  # type: ignore[type-abstract]

        handler = NodeExecutionSaveResultHandler(sql_uow, clock, id_generator)
        await handler.handle(
            SaveNodeExecutionResultCommand(
                workflow_id="wf-sql-nr-1",
                node_execution_id="node-sql-nr-1",
                status="done",
                stdout="success",
                stderr="",
                artifact_uri="",
            )
        )

        q = NodeExecutionGetResultHandler(NodeResultQueryService(session_factory))
        dto = await q.handle(NodeExecutionGetResultQuery("node-sql-nr-1", "wf-sql-nr-1"))
        assert dto is not None
        assert dto.stdout == "success"
        assert dto.status == "done"
