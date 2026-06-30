from __future__ import annotations

import pytest

from shell.domain.execution.events import WorkflowAbortedEvent
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.tests.conftest_helpers import _NOW, _new_workflow


class TestAbort:
    def test_abort_from_active_transitions_to_aborted(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.pull_events()
        wf.abort(reason="boom", now=_NOW, task_execution_id=TaskExecutionId("task-456"))
        assert wf.status == WorkflowStatus.ABORTED
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowAbortedEvent) for e in events)

    def test_abort_from_active_without_task_execution_id_emits_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.pull_events()
        wf.abort(reason="boom", now=_NOW)
        assert wf.status == WorkflowStatus.ABORTED
        events = wf.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], WorkflowAbortedEvent)

    def test_abort_from_active_transitions_to_aborted_directly(self) -> None:
        wf = _new_workflow()
        wf.abort(reason="boom", now=_NOW)
        assert wf.status == WorkflowStatus.ABORTED

    def test_abort_from_completed_raises(self) -> None:
        wf = _new_workflow()
        wf.finish(now=_NOW)
        wf.pull_events()
        with pytest.raises(InvalidWorkflowTransition):
            wf.abort(reason="late", now=_NOW)
