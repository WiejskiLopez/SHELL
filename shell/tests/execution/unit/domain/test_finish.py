from __future__ import annotations

import pytest
from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.tests.conftest import _NOW, _new_workflow


class TestFinish:
    def test_active_to_completed_with_task_execution_id_emits_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.pull_events()
        wf.finish(now=_NOW, task_execution_id=TaskExecutionId("task-456"))
        assert wf.status == WorkflowStatus.COMPLETED
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowCompletedEvent) for e in events)

    def test_active_to_completed_without_task_execution_id_emits_no_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.pull_events()
        wf.finish(now=_NOW)
        assert wf.status == WorkflowStatus.COMPLETED
        assert wf.pull_events() == []

    def test_finish_from_completed_raises(self) -> None:
        wf = _new_workflow()
        wf.finish(now=_NOW)
        with pytest.raises(InvalidWorkflowTransition):
            wf.finish(now=_NOW)
