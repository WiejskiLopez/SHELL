"""Workflow aggregate."""

from shell.domain.aggregates.workflow.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.aggregates.workflow.workflow import Workflow

__all__ = [
    "GraphNodeExecutionState",
    "Workflow",
]
