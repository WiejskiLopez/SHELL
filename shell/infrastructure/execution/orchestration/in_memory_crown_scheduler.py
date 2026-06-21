"""InMemoryCrownScheduler — in-memory implementation for testing."""

from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution.ports.crown_scheduler import (
    CrownScheduler,
    SubGraphChildStatus,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorach i sygnaturach metod CrownScheduler
)


class InMemoryCrownScheduler(CrownScheduler):
    """In-memory CrownScheduler for unit tests."""

    def __init__(self) -> None:
        self._children: dict[str, dict[str, SubGraphChildStatus]] = {}  # parent_id -> {child_id -> status}
        self._waiting: set[str] = set()

    async def register_child(
        self,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
    ) -> None:
        parent_key = parent_graph_execution_id.value
        child_key = child_graph_execution_id.value
        if parent_key not in self._children:
            self._children[parent_key] = {}
        self._children[parent_key][child_key] = SubGraphChildStatus(
            parent_graph_execution_id=parent_graph_execution_id,
            child_graph_execution_id=child_graph_execution_id,
            status="pending",
        )

    async def mark_waiting(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> None:
        self._waiting.add(graph_execution_id.value)

    async def on_child_completed(
        self,
        child_graph_execution_id: GraphExecutionId,
        result: dict | None = None,
    ) -> list[SubGraphChildStatus]:
        child_key = child_graph_execution_id.value
        for _parent_key, children in self._children.items():
            if child_key in children:
                children[child_key].status = "completed"
                children[child_key].result = result or {}
                return list(children.values())
        return []

    async def on_child_failed(
        self,
        child_graph_execution_id: GraphExecutionId,
        error: str = "",
    ) -> list[SubGraphChildStatus]:
        child_key = child_graph_execution_id.value
        for _parent_key, children in self._children.items():
            if child_key in children:
                children[child_key].status = "failed"
                return list(children.values())
        return []

    async def get_pending_children(
        self,
        parent_graph_execution_id: GraphExecutionId,
    ) -> list[GraphExecutionId]:
        parent_key = parent_graph_execution_id.value
        children = self._children.get(parent_key, {})
        return [
            status.child_graph_execution_id
            for status in children.values()
            if status.status == "pending"
        ]

    async def has_all_children_completed(
        self,
        parent_graph_execution_id: GraphExecutionId,
    ) -> bool:
        parent_key = parent_graph_execution_id.value
        children = self._children.get(parent_key, {})
        if not children:
            return True
        return all(s.status in ("completed", "failed") for s in children.values())

    async def get_children(
        self,
        parent_graph_execution_id: GraphExecutionId,
    ) -> list[SubGraphChildStatus]:
        parent_key = parent_graph_execution_id.value
        return list(self._children.get(parent_key, {}).values())
