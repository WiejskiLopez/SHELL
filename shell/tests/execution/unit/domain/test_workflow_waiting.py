"""Tests for Workflow.wait_for_children / on_children_completed."""

from __future__ import annotations

from datetime import datetime, timezone

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.execution.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell.domain.platform.value_objects.status import Status


_NOW = datetime.now(timezone.utc)


class TestWorkflowWaitingState:
    def test_wait_for_children_marks_node_as_waiting(self) -> None:
        workflow = self._make_running_workflow()
        node_id = GraphNodeExecutionId("node-1")

        workflow.wait_for_children(
            graph_node_execution_id=node_id,
            child_graph_ids=["child-1", "child-2"],
            now=_NOW,
        )

        state = workflow.get_graph_node_execution_state(node_id)
        assert state is not None
        assert state.status == Status.waiting()

        assert node_id.value in workflow.waiting_nodes
        assert workflow.waiting_nodes[node_id.value] == ["child-1", "child-2"]

    def test_on_children_completed_marks_node_done(self) -> None:
        workflow = self._make_running_workflow()
        node_id = GraphNodeExecutionId("node-1")
        workflow.wait_for_children(
            graph_node_execution_id=node_id,
            child_graph_ids=["child-1"],
            now=_NOW,
        )

        workflow.on_children_completed(
            graph_node_execution_id=node_id,
            now=_NOW,
        )

        state = workflow.get_graph_node_execution_state(node_id)
        assert state is not None
        assert state.status == Status.done()

        assert node_id.value not in workflow.waiting_nodes

    def test_wait_for_children_requires_running_status(self) -> None:
        from shell.domain.execution.exceptions import InvalidWorkflowTransition

        workflow = Workflow.new(
            id_=WorkflowId("wf-1"),
            task_execution_id=TaskExecutionId("task-1"),
            now=_NOW,
        )
        node_id = GraphNodeExecutionId("node-1")

        raised = False
        try:
            workflow.wait_for_children(
                graph_node_execution_id=node_id,
                now=_NOW,
            )
        except InvalidWorkflowTransition:
            raised = True

        assert raised, "Expected InvalidWorkflowTransition for idle workflow"

    def _make_running_workflow(self) -> Workflow:
        workflow = Workflow.new(
            id_=WorkflowId("wf-1"),
            task_execution_id=TaskExecutionId("task-1"),
            now=_NOW,
        )
        workflow.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("start"),
            context=WorkflowExecutionContext(correlation_id="corr-1"),
            now=_NOW,
        )
        return workflow
