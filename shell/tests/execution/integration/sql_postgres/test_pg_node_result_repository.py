from __future__ import annotations

from shell.application.execution.command_handlers.node_execution_save_result_handler import (
    NodeExecutionSaveResultHandler,
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


class TestPgNodeResultRepository:
    async def test_save_and_get_result(
        self,
        sql_uow,
        clock,
        id_gen,
        events,
        session_factory,
    ) -> None:
        async with sql_uow as u:
            await u.repository(WorkflowRepository).save(
                Workflow.new(id_=WorkflowId("pg-wf-nr-1"), now=clock.now())
            )
            node = NodeExecution(
                id=NodeExecutionId("pg-node-nr-1"),
                position=NodeOrder(0),
                mode=Mode.WORKER,
                role=NodeRole.AGENT,
                node_type=NodeType("worker"),
            )
            await u.repository(NodeExecutionRepository).save(node)

        NodeExecutionSaveResultHandler(sql_uow, clock, id_gen)

        q = NodeExecutionGetResultHandler(NodeResultQueryService(session_factory))
        dto = await q.handle(NodeExecutionGetResultQuery("pg-node-nr-1", "pg-wf-nr-1"))
        assert dto is not None
        assert dto.stdout == "pg success"
        assert dto.status == "done"
