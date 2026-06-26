"""Unit tests for SaveGraphNodeExecutionResultHandler."""

from __future__ import annotations

from shell.application.execution.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.platform.commands.commands import SaveGraphNodeExecutionResultCommand
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.platform.value_objects.mode import Mode


class TestSaveGraphNodeExecutionResultHandler:
    async def test_happy_path(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        wf = Workflow.new(id_=WorkflowId("wf-1"), now=clock.now())
        await unit_of_work.workflow_repository.save(wf)

        node = GraphNodeExecution(
            id=GraphNodeExecutionId("node-1"),
            position=0,
            mode=Mode.WORKER,
            role="worker",
            node_type="worker",
        )
        await unit_of_work.graph_node_execution_repository.save(node)

        handler = SaveGraphNodeExecutionResultHandler(unit_of_work, clock, id_generator)
        result_id = await handler.handle(
            SaveGraphNodeExecutionResultCommand(
                workflow_id="wf-1",
                graph_node_execution_id="node-1",
                status="done",
                stdout="ok",
            )
        )
        assert result_id

        states = await unit_of_work.graph_node_execution_state_repository.list_by_graph_node_execution_and_kind(
            GraphNodeExecutionId("node-1"), StateKind.OUTPUT
        )
        assert len(states) > 0
        assert states[-1].state_data.get("stdout") == "ok"
