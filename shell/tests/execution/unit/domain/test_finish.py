from __future__ import annotations

import pytest

from shell.domain.execution.events import WorkflowCompletedEvent
from shell.domain.exceptions import InvalidWorkflowTransition
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId, GraphNodeExecutionResultId
from shell.domain.platform.value_objects.status import Status
from shell.domain.execution.value_objects.workflow_cursor import WorkflowCursor
from shell.tests.unit.domain.conftest import _ctx, _new_workflow, _NOW


class TestFinish:
    def test_finish_transitions_to_done_and_clears_cursor(self) -> None:
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
        wf.finish(_NOW)
        assert wf.status == Status.done()
        assert wf.cursor == WorkflowCursor.empty()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowCompletedEvent) for e in events)

    def test_finish_from_idle_raises(self) -> None:
        wf = _new_workflow()
        with pytest.raises(InvalidWorkflowTransition):
            wf.finish(_NOW)
