from __future__ import annotations

from shell.application.execution.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.platform.commands.commands import SaveGraphNodeExecutionResultCommand
from shell.application.platform.queries.queries import GetGraphNodeExecutionResultQuery
from shell.application.platform.query_handlers.query_handlers import (
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
            await u.workflow_repository.save(
                Workflow.new(id_=WorkflowId("pg-wf-nr-1"), now=clock.now())
            )
            node = GraphNodeExecution(
                id=GraphNodeExecutionId("pg-node-nr-1"),
                position=NodeOrder(0),
                mode=Mode.WORKER,
                role="worker",
                node_type=NodeType("worker"),
            )
            await u.graph_node_execution_repository.save(node)

        handler = SaveGraphNodeExecutionResultHandler(sql_uow, clock, id_gen)

        q = GetGraphNodeExecutionResultHandler(NodeResultQueryService(session_factory))
        dto = await q.handle(GetGraphNodeExecutionResultQuery("pg-node-nr-1", "pg-wf-nr-1"))
        assert dto is not None
        assert dto.stdout == "pg success"
        assert dto.status == "done"
