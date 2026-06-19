"""Unit tests for ``WorkflowCursor`` construction."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from shell.domain.execution.value_objects.ids import GraphNodeExecutionId
from shell.domain.execution.value_objects.workflow_cursor import WorkflowCursor


class TestWorkflowCursorConstruction:
    def test_empty_factory_yields_inactive_cursor(self) -> None:
        cur = WorkflowCursor.empty()
        assert cur.current_graph_node_execution_id is None
        assert cur.is_active() is False

    def test_at_factory_points_to_node(self) -> None:
        node = GraphNodeExecutionId("step-1")
        cur = WorkflowCursor.at(node)
        assert cur.current_graph_node_execution_id == node
        assert cur.is_active() is True

    def test_cursor_is_immutable(self) -> None:
        cur = WorkflowCursor.at(GraphNodeExecutionId("x"))
        with pytest.raises(FrozenInstanceError):
            cur.current_graph_node_execution_id = GraphNodeExecutionId("y")  # type: ignore[attr-defined]
