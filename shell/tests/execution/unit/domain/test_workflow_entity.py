"""Unit tests for Workflow entity."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    TaskExecutionId,
    WorkflowId
)

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestWorkflow:
    def test_new_workflow_is_idle(self) -> None:
        wf = Workflow.new(
            id_=WorkflowId.generate(), now=_NOW
        )
        assert wf.status.value == "idle"

    def test_start_at_sets_running(self) -> None:
        from shell.domain.execution.value_objects.workflow_execution_context import (
            WorkflowExecutionContext,
        )

        wf = Workflow.new(
            id_=WorkflowId.generate(), now=_NOW
        )
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"),
            context=WorkflowExecutionContext.empty(),
            now=_NOW,
        )
        assert wf.status.value == "running"
        assert wf.cursor.current_graph_node_execution_id == GraphNodeExecutionId("n1")

    def test_update_graph_node_execution_state(self) -> None:
        from shell.domain.platform.value_objects.status import Status

        wf = Workflow.new(
            id_=WorkflowId.generate(), now=_NOW
        )
        graph_node_execution_id = GraphNodeExecutionId("node-1")
        wf.update_graph_node_execution_state(
            graph_node_execution_id, Status.running(), now=_NOW, step=2
        )
        state = wf.get_graph_node_execution_state(graph_node_execution_id)
        assert state is not None
        assert state.step == 2
