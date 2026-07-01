"""Unit tests for GraphNodeExecutionSaveResultHandler."""

from __future__ import annotations

from shell.application.execution.command_handlers.graph_node_execution_save_result_handler import (
    GraphNodeExecutionSaveResultHandler,
)
from shell.application.execution.commands.graph_node_execution_commands import (
    SaveGraphNodeExecutionResultCommand,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, WorkflowId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_repository import (
    InMemoryGraphNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_state_repository import (
    InMemoryGraphNodeExecutionStateRepository,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
    InMemoryWorkflowRepository,
)


class TestGraphNodeExecutionSaveResultHandler:
    async def test_happy_path(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        wf = Workflow.new(id_=WorkflowId("wf-1"), now=clock.now())
        await unit_of_work.repository(InMemoryWorkflowRepository).save(wf)

        node = GraphNodeExecution(
            id=GraphNodeExecutionId("node-1"),
            position=NodeOrder(0),
            mode=Mode.WORKER,
            role=NodeRole.AGENT,
            node_type=NodeType("worker"),
        )
        await unit_of_work.repository(InMemoryGraphNodeExecutionRepository).save(node)

        handler = GraphNodeExecutionSaveResultHandler(unit_of_work, clock, id_generator)
        result_id = await handler.handle(
            SaveGraphNodeExecutionResultCommand(
                workflow_id="wf-1",
                graph_node_execution_id="node-1",
                status="done",
                stdout="ok",
                stderr="",
                artifact_uri="",
            )
        )
        assert result_id

        states = await unit_of_work.repository(
            InMemoryGraphNodeExecutionStateRepository
        ).list_by_graph_node_execution_and_direction(
            GraphNodeExecutionId("node-1"), StateDirection.OUT
        )
        assert len(states) > 0
        assert states[-1].state_data.get("stdout") == "ok"
