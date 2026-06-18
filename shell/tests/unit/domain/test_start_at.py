from __future__ import annotations

import pytest

from shell.domain.events.events import GraphNodeExecutionStarted, WorkflowStarted
from shell.domain.exceptions import InvalidWorkflowTransition
from shell.domain.value_objects.ids import GraphNodeExecutionId
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.workflow_cursor import WorkflowCursor
from shell.tests.unit.domain.conftest import _ctx, _new_workflow, _NOW


class TestStartAt:
    def test_idle_to_running_sets_cursor_and_emits_events(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        assert wf.status == Status.running()
        assert wf.cursor == WorkflowCursor.at(GraphNodeExecutionId("n1"))
        assert wf.execution_context == _ctx()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStarted) for e in events)
        assert any(isinstance(e, GraphNodeExecutionStarted) for e in events)

    def test_double_start_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        with pytest.raises(InvalidWorkflowTransition):
            wf.start_at(
                first_graph_node_execution_id=GraphNodeExecutionId("n2"), context=_ctx(), now=_NOW
            )
