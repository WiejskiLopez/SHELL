"""Unit tests for ``WorkflowCursor`` value object.

WorkflowCursor is the execution pointer that lets the worker know which node
should be processed next. The VO must be immutable, comparable by value, and
expose a small algebra (``empty``, ``at``, ``cleared``, ``points_to``,
``is_active``).
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from shell_ddd.domain.value_objects.ids import NodeId
from shell_ddd.domain.value_objects.workflow_cursor import WorkflowCursor


class TestWorkflowCursorConstruction:
    def test_empty_factory_yields_inactive_cursor(self) -> None:
        cur = WorkflowCursor.empty()
        assert cur.current_node_id is None
        assert cur.is_active() is False

    def test_at_factory_points_to_node(self) -> None:
        node = NodeId("step-1")
        cur = WorkflowCursor.at(node)
        assert cur.current_node_id == node
        assert cur.is_active() is True

    def test_cursor_is_immutable(self) -> None:
        cur = WorkflowCursor.at(NodeId("x"))
        with pytest.raises(FrozenInstanceError):
            cur.current_node_id = NodeId("y")  # type: ignore[misc]


class TestWorkflowCursorAlgebra:
    def test_points_to_matches_only_current_node(self) -> None:
        cur = WorkflowCursor.at(NodeId("alpha"))
        assert cur.points_to(NodeId("alpha")) is True
        assert cur.points_to(NodeId("beta")) is False

    def test_points_to_on_empty_cursor_is_always_false(self) -> None:
        cur = WorkflowCursor.empty()
        assert cur.points_to(NodeId("anything")) is False

    def test_cleared_returns_empty_cursor(self) -> None:
        cur = WorkflowCursor.at(NodeId("step-1")).cleared()
        assert cur == WorkflowCursor.empty()
        assert cur.is_active() is False

    def test_value_equality(self) -> None:
        a = WorkflowCursor.at(NodeId("n"))
        b = WorkflowCursor.at(NodeId("n"))
        c = WorkflowCursor.at(NodeId("m"))
        assert a == b
        assert a != c
