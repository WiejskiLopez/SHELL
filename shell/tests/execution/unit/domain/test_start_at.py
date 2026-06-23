from __future__ import annotations

import pytest
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.tests.conftest import _NOW, _new_workflow


class TestStartAt:
    def test_active_start_with_task_execution_id_emits_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW, task_execution_id=TaskExecutionId("task-456"))
        assert wf.status == WorkflowStatus.ACTIVE
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStartedEvent) for e in events)

    def test_active_start_without_task_execution_id_emits_no_event(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        assert wf.status == WorkflowStatus.ACTIVE
        assert wf.pull_events() == []

    def test_double_start_is_idempotent(self) -> None:
        wf = _new_workflow()
        wf.start_at(now=_NOW)
        wf.start_at(now=_NOW)  # idempotent — already ACTIVE
