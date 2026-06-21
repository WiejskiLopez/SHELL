from __future__ import annotations

import pytest
from shell.domain.execution.events import (
    GraphNodeExecutionAdvancedEvent,
    GraphNodeExecutionStartedEvent,
)
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.workflow_cursor import WorkflowCursor
from shell.domain.platform.value_objects.status import Status
from shell.tests.conftest import _NOW, _ctx, _new_workflow


class TestAdvanceTo:
    def test_advance_moves_cursor_and_emits_events(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        wf.record_graph_node_execution_result(
            result_id=GraphNodeExecutionResultId.generate(),
            graph_node_execution_id=GraphNodeExecutionId("n1"),
            status=Status.done(),
            now=_NOW,
        )
        wf.pull_events()
        wf.advance_to(next_graph_node_execution_id=GraphNodeExecutionId("n2"), now=_NOW)
        assert wf.cursor == WorkflowCursor.at(GraphNodeExecutionId("n2"))
        events = wf.pull_events()
        assert any(isinstance(e, GraphNodeExecutionAdvancedEvent) for e in events)
        assert any(isinstance(e, GraphNodeExecutionStartedEvent) for e in events)

    def test_advance_requires_running_status(self) -> None:
        wf = _new_workflow()
        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_graph_node_execution_id=GraphNodeExecutionId("n2"), now=_NOW)

    def test_advance_requires_active_cursor(self) -> None:
        wf = _new_workflow()
        wf._status = Status.running()
        wf._cursor = WorkflowCursor.empty()
        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_graph_node_execution_id=GraphNodeExecutionId("n2"), now=_NOW)
