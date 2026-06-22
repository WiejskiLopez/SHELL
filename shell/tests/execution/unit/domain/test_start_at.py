from __future__ import annotations

import pytest
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.platform.value_objects.status import Status
from shell.tests.conftest import _NOW, _new_workflow


class TestStartAt:
    def test_idle_to_running_with_task_execution_id_emits_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW, task_execution_id=TaskExecutionId("task-456"))
        assert wf.status == Status.running()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStartedEvent) for e in events)

    def test_idle_to_running_without_task_execution_id_emits_no_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        assert wf.status == Status.running()
        assert wf.pull_events() == []

    def test_double_start_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        with pytest.raises(InvalidWorkflowTransition):
            wf.start_at(now=_NOW)
