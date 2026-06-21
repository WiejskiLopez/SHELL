from __future__ import annotations

from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
)
from shell.domain.execution.value_objects.workflow_cursor import WorkflowCursor
from shell.domain.platform.value_objects.status import Status
from shell.tests.conftest import _NOW, _ctx, _new_workflow


class TestRecordGraphNodeExecutionResult:
    def test_recording_does_not_move_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        wf.pull_events()
        wf.record_graph_node_execution_result(
            result_id=GraphNodeExecutionResultId.generate(),
            graph_node_execution_id=GraphNodeExecutionId("n1"),
            status=Status.done(),
            now=_NOW,
            stdout="ok",
        )
        assert wf.cursor == WorkflowCursor.at(GraphNodeExecutionId("n1"))
        events = wf.pull_events()
        assert any(isinstance(e, GraphNodeExecutionCompletedEvent) for e in events)

    def test_recording_failure_emits_node_failed(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        wf.pull_events()
        wf.record_graph_node_execution_result(
            result_id=GraphNodeExecutionResultId.generate(),
            graph_node_execution_id=GraphNodeExecutionId("n1"),
            status=Status.failed(),
            now=_NOW,
            stderr="boom",
            reason="boom",
        )
        events = wf.pull_events()
        assert any(isinstance(e, GraphNodeExecutionFailedEvent) for e in events)
