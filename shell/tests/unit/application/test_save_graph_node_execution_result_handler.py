"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from shell.application.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.commands.commands import SaveGraphNodeExecutionResultCommand
from shell.application.queries.queries import GetGraphNodeExecutionResultQuery
from shell.application.query_handlers.query_handlers import GetGraphNodeExecutionResultHandler
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)


class TestSaveGraphNodeExecutionResultHandler:
    async def test_happy_path(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        from shell.domain.aggregates.workflow import Workflow
        from shell.domain.value_objects.ids import TaskExecutionId, WorkflowId

        wf = Workflow.new(
            id_=WorkflowId("wf-1"), task_execution_id=TaskExecutionId("task-1"), now=clock.now()
        )
        await uow.workflows.save(wf)

        handler = SaveGraphNodeExecutionResultHandler(uow, clock, id_gen)
        result_id = await handler.handle(
            SaveGraphNodeExecutionResultCommand(
                workflow_id="wf-1",
                graph_node_execution_id="node-1",
                status="done",
                stdout="ok",
            )
        )
        assert result_id
        q_handler = GetGraphNodeExecutionResultHandler(queries)
        dto = await q_handler.handle(GetGraphNodeExecutionResultQuery("node-1", "wf-1"))
        assert dto is not None
        assert dto.stdout == "ok"
