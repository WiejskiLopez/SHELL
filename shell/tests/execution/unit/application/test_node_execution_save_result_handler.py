"""Unit tests for NodeExecutionSaveResultHandler."""

from __future__ import annotations

from shell.application.execution.command_handlers.node_execution_save_result_handler import (
    NodeExecutionSaveResultHandler,
)
from shell.application.execution.commands.node_execution_commands import (
    SaveNodeExecutionResultCommand,
)
from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.ids import NodeExecutionId, WorkflowId
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_node_execution_state_repository import (
    InMemoryNodeExecutionStateRepository,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
    InMemoryWorkflowRepository,
)


class TestNodeExecutionSaveResultHandler:
    async def test_happy_path(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        wf = Workflow.new(id_=WorkflowId("wf-1"), now=clock.now())
        await unit_of_work.repository(InMemoryWorkflowRepository).save(wf)

        node = NodeExecution(
            id=NodeExecutionId("node-1"),
            position=NodeOrder(0),
            mode=Mode.WORKER,
            role=NodeRole.AGENT,
            node_type=NodeType("worker"),
        )
        await unit_of_work.repository(InMemoryNodeExecutionRepository).save(node)

        handler = NodeExecutionSaveResultHandler(unit_of_work, clock, id_generator)
        result_id = await handler.handle(
            SaveNodeExecutionResultCommand(
                workflow_id="wf-1",
                node_execution_id="node-1",
                status="done",
                stdout="ok",
                stderr="",
                artifact_uri="",
            )
        )
        assert result_id

        states = await unit_of_work.repository(
            InMemoryNodeExecutionStateRepository
        ).list_by_node_execution_and_direction(
            NodeExecutionId("node-1"), StateDirection.OUT
        )
        assert len(states) > 0
        assert states[-1].state_data.get("stdout") == "ok"
