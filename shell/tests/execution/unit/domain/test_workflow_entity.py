from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.created_at import CreatedAt

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
_NOW_CREATED_AT = CreatedAt.from_datetime(_NOW)


class TestWorkflow:
    def test_new_workflow_is_active(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        assert wf.status == WorkflowStatus.ACTIVE

    def test_start_at_keeps_active(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        wf.start_at(now=_NOW, task_execution_id=TaskExecutionId("t1"))

        assert wf.status == WorkflowStatus.ACTIVE
        assert wf.created_at == _NOW_CREATED_AT

    def test_finish_sets_completed(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        wf.start_at(now=_NOW)
        wf.finish(now=_NOW)

        assert wf.status == WorkflowStatus.COMPLETED

    def test_abort_sets_aborted(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        wf.start_at(now=_NOW)
        wf.abort(reason="test", now=_NOW)

        assert wf.status == WorkflowStatus.ABORTED
