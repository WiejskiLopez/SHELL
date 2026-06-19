"""Unit tests for ``WorkflowCursor`` algebra."""

from __future__ import annotations

from shell.domain.execution.value_objects.ids import GraphNodeExecutionId
from shell.domain.execution.value_objects.workflow_cursor import WorkflowCursor


class TestWorkflowCursorAlgebra:
    def test_points_to_matches_only_current_node(self) -> None:
        cur = WorkflowCursor.at(GraphNodeExecutionId("alpha"))
        assert cur.points_to(GraphNodeExecutionId("alpha")) is True
        assert cur.points_to(GraphNodeExecutionId("beta")) is False

    def test_points_to_on_empty_cursor_is_always_false(self) -> None:
        cur = WorkflowCursor.empty()
        assert cur.points_to(GraphNodeExecutionId("anything")) is False

    def test_cleared_returns_empty_cursor(self) -> None:
        cur = WorkflowCursor.at(GraphNodeExecutionId("step-1")).cleared()
        assert cur == WorkflowCursor.empty()
        assert cur.is_active() is False

    def test_value_equality(self) -> None:
        a = WorkflowCursor.at(GraphNodeExecutionId("n"))
        b = WorkflowCursor.at(GraphNodeExecutionId("n"))
        c = WorkflowCursor.at(GraphNodeExecutionId("m"))
        assert a == b
        assert a != c
