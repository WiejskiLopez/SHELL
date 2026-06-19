"""Workflow aggregate."""
from __future__ import annotations

from shell.domain.execution.aggregates.workflow.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.execution.aggregates.workflow.workflow import Workflow

__all__ = [
    "GraphNodeExecutionState",
    "Workflow",
]
