from __future__ import annotations

import pytest

from shell.domain.events.events import GraphNodeExecutionAdvanced, GraphNodeExecutionStarted
from shell.domain.exceptions import InvalidWorkflowTransition
from shell.domain.value_objects.ids import GraphNodeExecutionId, GraphNodeExecutionResultId
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.workflow_cursor import WorkflowCursor
from shell.tests.unit.domain.conftest import _ctx, _new_workflow, _NOW


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
        assert any(isinstance(e, GraphNodeExecutionAdvanced) for e in events)
        assert any(isinstance(e, GraphNodeExecutionStarted) for e in events)

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
