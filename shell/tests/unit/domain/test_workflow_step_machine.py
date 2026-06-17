"""Unit tests for the ``Workflow`` step-by-step state machine.

The aggregate exposes four primary state-changing methods:
``start_at`` → ``record_node_result`` → (``advance_to`` | ``finish`` | ``abort``)

These tests assert:
- valid transitions emit the correct event sequence,
- invalid transitions raise :class:`InvalidWorkflowTransition`,
- the cursor is set/cleared at the right moments,
- ``record_node_result`` does **not** move the cursor.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.domain.entities.workflow import Workflow
from shell.domain.events.events import (
    NodeAdvanced,
    NodeCompleted,
    NodeFailed,
    NodeStarted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from shell.domain.exceptions import InvalidWorkflowTransition
from shell.domain.value_objects.ids import NodeId, NodeResultId, TaskExecutionId, WorkflowId
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.workflow_cursor import WorkflowCursor
from shell.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _new_workflow() -> Workflow:
    return Workflow.new(id_=WorkflowId.generate(), task_execution_id=TaskExecutionId("task-id"), now=_NOW)


def _ctx() -> WorkflowExecutionContext:
    return WorkflowExecutionContext(work_dir="/tmp", correlation_id="cid-1")


class TestStartAt:
    def test_idle_to_running_sets_cursor_and_emits_events(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)

        assert wf.status == Status.running()
        assert wf.cursor == WorkflowCursor.at(NodeId("n1"))
        assert wf.execution_context == _ctx()

        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStarted) for e in events)
        assert any(isinstance(e, NodeStarted) for e in events)

    def test_double_start_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        with pytest.raises(InvalidWorkflowTransition):
            wf.start_at(first_node_id=NodeId("n2"), context=_ctx(), now=_NOW)


class TestRecordNodeResult:
    def test_recording_does_not_move_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
            stdout="ok",
        )

        assert wf.cursor == WorkflowCursor.at(NodeId("n1"))
        events = wf.pull_events()
        assert any(isinstance(e, NodeCompleted) for e in events)

    def test_recording_failure_emits_node_failed(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.failed(),
            now=_NOW,
            stderr="boom",
            reason="boom",
        )

        events = wf.pull_events()
        assert any(isinstance(e, NodeFailed) for e in events)


class TestAdvanceTo:
    def test_advance_moves_cursor_and_emits_events(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
        )
        wf.pull_events()

        wf.advance_to(next_node_id=NodeId("n2"), now=_NOW)

        assert wf.cursor == WorkflowCursor.at(NodeId("n2"))
        events = wf.pull_events()
        assert any(isinstance(e, NodeAdvanced) for e in events)
        assert any(isinstance(e, NodeStarted) for e in events)

    def test_advance_requires_running_status(self) -> None:
        wf = _new_workflow()
        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_node_id=NodeId("n2"), now=_NOW)

    def test_advance_requires_active_cursor(self) -> None:
        wf = _new_workflow()
        # Reach the otherwise-unreachable "running with no cursor" state by
        # directly mutating the aggregate. This guards against future code
        # paths that might bypass ``start_at`` and leave the cursor empty.
        wf.status = Status.running()
        wf.cursor = WorkflowCursor.empty()
        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_node_id=NodeId("n2"), now=_NOW)


class TestFinish:
    def test_finish_transitions_to_done_and_clears_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
        )
        wf.pull_events()

        wf.finish(_NOW)

        assert wf.status == Status.done()
        assert wf.cursor == WorkflowCursor.empty()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowCompleted) for e in events)

    def test_finish_from_idle_raises(self) -> None:
        wf = _new_workflow()
        with pytest.raises(InvalidWorkflowTransition):
            wf.finish(_NOW)


class TestAbort:
    def test_abort_transitions_to_failed_and_clears_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.abort(reason="boom", now=_NOW)

        assert wf.status == Status.failed()
        assert wf.cursor == WorkflowCursor.empty()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowFailed) for e in events)

    def test_abort_from_done_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
        )
        wf.finish(_NOW)
        wf.pull_events()

        with pytest.raises(InvalidWorkflowTransition):
            wf.abort(reason="late", now=_NOW)

    def test_abort_invokes_compensation_handler(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        called: list[tuple[Workflow, str]] = []

        class _SpyCompensation:
            def compensate(self, workflow: Workflow, reason: str) -> None:
                called.append((workflow, reason))

        wf.abort(reason="boom", now=_NOW, compensation=_SpyCompensation())

        assert called == [(wf, "boom")]
