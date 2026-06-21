from __future__ import annotations

import pytest
from shell.domain.execution.aggregates.graph_node_execution.value_objects.workflow_cursor import (
    WorkflowCursor,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.events import WorkflowFailedEvent
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    TaskExecutionId,
)
from shell.domain.platform.value_objects.status import Status
from shell.tests.conftest import _NOW, _ctx, _new_workflow


class TestAbort:
    def test_abort_transitions_to_failed_and_clears_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        wf.pull_events()
        wf.abort(reason="boom", now=_NOW, task_execution_id=TaskExecutionId("task-456"))
        assert wf.status == Status.failed()
        assert wf.cursor == WorkflowCursor.empty()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowFailedEvent) for e in events)

    def test_abort_from_done_raises(self) -> None:
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
        wf.finish(_NOW)
        wf.pull_events()
        with pytest.raises(InvalidWorkflowTransition):
            wf.abort(reason="late", now=_NOW)

    def test_abort_invokes_compensation_handler(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        wf.pull_events()
        called: list[tuple[Workflow, str]] = []

        class _SpyCompensation:
            def compensate(self, workflow: Workflow, reason: str) -> None:
                called.append((workflow, reason))

        wf.abort(reason="boom", now=_NOW, compensation=_SpyCompensation())
        assert called == [(wf, "boom")]
