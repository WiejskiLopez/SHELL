from __future__ import annotations

from shell.application.execution.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.platform.commands.commands import SaveGraphNodeExecutionResultCommand
from shell.application.platform.queries.queries import GetGraphNodeExecutionResultQuery
from shell.application.platform.query_handlers.query_handlers import (
    GetGraphNodeExecutionResultHandler,
)
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
        handler = SaveGraphNodeExecutionResultHandler(sql_uow, clock, id_gen)
        await handler.handle(
            SaveGraphNodeExecutionResultCommand(
                workflow_id="pg-wf-nr-1",
                graph_node_execution_id="pg-node-nr-1",
                status="done",
                stdout="pg success",
            )
        )

        q = GetGraphNodeExecutionResultHandler(NodeResultQueryService(session_factory))
        dto = await q.handle(GetGraphNodeExecutionResultQuery("pg-node-nr-1", "pg-wf-nr-1"))
        assert dto is not None
        assert dto.stdout == "pg success"
        assert dto.status == "done"
