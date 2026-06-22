from __future__ import annotations

import pytest
from shell.domain.execution.aggregates.workflow.events.workflow_failed_event import (
    WorkflowFailedEvent,
)
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.platform.value_objects.status import Status
from shell.tests.conftest import _NOW, _new_workflow


class TestAbort:
    def test_abort_from_running_transitions_to_failed(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.pull_events()
        wf.abort(reason="boom", now=_NOW, task_execution_id=TaskExecutionId("task-456"))
        assert wf.status == Status.failed()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowFailedEvent) for e in events)

    def test_abort_from_running_without_task_execution_id_emits_no_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.pull_events()
        wf.abort(reason="boom", now=_NOW)
        assert wf.status == Status.failed()
        assert wf.pull_events() == []

    def test_abort_from_idle_transitions_to_failed(self) -> None:
        wf = _new_workflow()
        wf.abort(reason="boom", now=_NOW)
        assert wf.status == Status.failed()

    def test_abort_from_done_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.finish(now=_NOW)
        wf.pull_events()
        with pytest.raises(InvalidWorkflowTransition):
            wf.abort(reason="late", now=_NOW)
