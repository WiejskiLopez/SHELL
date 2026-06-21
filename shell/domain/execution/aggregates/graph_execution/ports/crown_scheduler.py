"""CrownScheduler — orchestrates parent-child graph execution lifecycle.

Tracks which graph executions are waiting for child sub-graphs to complete.
Notifies parent when all children are done.
"""

from __future__ import annotations

from typing import Any, Protocol

from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorze SubGraphChildStatus i sygnaturach Protocol
)


class SubGraphChildStatus:
    """Runtime status of a sub-graph child relationship."""

    __slots__ = (
        "parent_graph_execution_id",
        "child_graph_execution_id",
        "status",
        "result",
    )

    def __init__(
        self,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
        status: str = "pending",
        result: dict[str, Any] | None = None,
    ) -> None:
        self.parent_graph_execution_id = parent_graph_execution_id
        self.child_graph_execution_id = child_graph_execution_id
        self.status = status
        self.result = result or {}


class CrownScheduler(Protocol):
    """Orchestrates parent-child graph execution lifecycle.

    Implementations are infrastructure adapters (database, in-memory).
    """

    async def register_child(
        self,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
    ) -> None:
        """Register a child sub-graph for a parent graph execution."""
        ...

    async def mark_waiting(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> None:
        """Mark a graph execution as waiting for its children."""
        ...

    async def on_child_completed(
        self,
        child_graph_execution_id: GraphExecutionId,
        result: dict[str, Any] | None = None,
    ) -> list[SubGraphChildStatus]:
        """Notify that a child sub-graph completed.

        Returns updated status of all children for the parent.
        """
        ...

    async def on_child_failed(
        self,
        child_graph_execution_id: GraphExecutionId,
        error: str = "",
    ) -> list[SubGraphChildStatus]:
        """Notify that a child sub-graph failed.

        Returns updated status of all children for the parent.
        """
        ...

    async def get_pending_children(
        self,
        parent_graph_execution_id: GraphExecutionId,
    ) -> list[GraphExecutionId]:
        """Get IDs of all children still pending for a parent."""
        ...

    async def has_all_children_completed(
        self,
        parent_graph_execution_id: GraphExecutionId,
    ) -> bool:
        """Check if all children of a parent have completed."""
        ...

    async def get_children(
        self,
        parent_graph_execution_id: GraphExecutionId,
    ) -> list[SubGraphChildStatus]:
        """Get all children (pending and completed) for a parent."""
        ...
