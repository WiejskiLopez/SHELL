from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.ids import WorkflowId
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.platform.value_objects.status import Status

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestWorkflow:
    def test_new_workflow_is_idle(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        assert wf.status == Status.idle()

    def test_start_at_sets_running(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        wf.start_at(now=_NOW, task_execution_id=TaskExecutionId("t1"))

        assert wf.status == Status.running()
        assert wf.created_at == _NOW

    def test_finish_sets_done(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        wf.start_at(now=_NOW)
        wf.finish(now=_NOW)

        assert wf.status == Status.done()

    def test_abort_sets_failed(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
        wf.start_at(now=_NOW)
        wf.abort(reason="test", now=_NOW)

        assert wf.status == Status.failed()
