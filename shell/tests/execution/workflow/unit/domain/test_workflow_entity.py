from __future__ import annotations

from datetime import UTC, datetime

from shell.execution.domain.execution.aggregates.session_execution.value_objects.project_id_ref import (
    ProjectIdRef,
)
from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution.domain.execution.aggregates.workflow import Workflow
from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_status import (
    WorkflowStatus,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
_NOW_CREATED_AT = CreatedAt.from_datetime(_NOW)
_SESSION_ID = SessionIdRef("test-session-1")
_PROJECT_ID = ProjectIdRef("test-project-1")


class TestWorkflow:
    def test_new_workflow_is_active(self) -> None:
        wf = Workflow.create(
            id_=WorkflowId.generate(),
            now=_NOW_CREATED_AT,
            session_id=_SESSION_ID,
            project_id=_PROJECT_ID,
        )
        assert wf.status == WorkflowStatus.ACTIVE

    def test_start_at_keeps_active(self) -> None:
        wf = Workflow.create(
            id_=WorkflowId.generate(),
            now=_NOW_CREATED_AT,
            session_id=_SESSION_ID,
            project_id=_PROJECT_ID,
        )
        wf.start_at(task_execution_id=TaskExecutionId("t1"))

        assert wf.status == WorkflowStatus.ACTIVE
        assert wf.created_at == _NOW_CREATED_AT

    def test_finish_sets_completed(self) -> None:
        wf = Workflow.create(
            id_=WorkflowId.generate(),
            now=_NOW_CREATED_AT,
            session_id=_SESSION_ID,
            project_id=_PROJECT_ID,
        )
        wf.start_at()
        wf.finish()

        assert wf.status == WorkflowStatus.COMPLETED

    def test_abort_sets_aborted(self) -> None:
        wf = Workflow.create(
            id_=WorkflowId.generate(),
            now=_NOW_CREATED_AT,
            session_id=_SESSION_ID,
            project_id=_PROJECT_ID,
        )
        wf.start_at()
        wf.abort(reason="test")

        assert wf.status == WorkflowStatus.ABORTED
