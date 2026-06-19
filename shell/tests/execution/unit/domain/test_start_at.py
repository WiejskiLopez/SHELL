from __future__ import annotations

import pytest

from shell.domain.execution.events import GraphNodeExecutionStartedEvent, WorkflowStartedEvent
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId, TaskExecutionId
from shell.domain.platform.value_objects.status import Status
from shell.domain.execution.value_objects.workflow_cursor import WorkflowCursor
from shell.tests.conftest import _ctx, _new_workflow, _NOW


class TestStartAt:
    def test_idle_to_running_sets_cursor_and_emits_events(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW,
            task_execution_id=TaskExecutionId("task-456"),
        )
        assert wf.status == Status.running()
        assert wf.cursor == WorkflowCursor.at(GraphNodeExecutionId("n1"))
        assert wf.execution_context == _ctx()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStartedEvent) for e in events)
        assert any(isinstance(e, GraphNodeExecutionStartedEvent) for e in events)

    def test_double_start_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("n1"), context=_ctx(), now=_NOW
        )
        with pytest.raises(InvalidWorkflowTransition):
            wf.start_at(
                first_graph_node_execution_id=GraphNodeExecutionId("n2"), context=_ctx(), now=_NOW
            )
