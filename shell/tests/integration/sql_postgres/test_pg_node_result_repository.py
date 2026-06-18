from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.commands.commands import SaveGraphNodeExecutionResultCommand
from shell.application.queries.queries import GetGraphNodeExecutionResultQuery
from shell.application.query_handlers.query_handlers import (
    GetGraphNodeExecutionResultHandler,
)
from shell.infrastructure.persistence.sql.query_services import SqlQueryServices



class TestPgNodeResultRepository:
    async def test_save_and_get_result(
        self,
        uow,
        clock,
        id_gen,
        events,
        session_factory,
    ) -> None:
        handler = SaveGraphNodeExecutionResultHandler(uow, clock, id_gen)
        await handler.handle(
            SaveGraphNodeExecutionResultCommand(
                workflow_id="pg-wf-nr-1",
                graph_node_execution_id="pg-node-nr-1",
                status="done",
                stdout="pg success",
            )
        )

        q = GetGraphNodeExecutionResultHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetGraphNodeExecutionResultQuery("pg-node-nr-1", "pg-wf-nr-1"))
        assert dto is not None
        assert dto.stdout == "pg success"
        assert dto.status == "done"
