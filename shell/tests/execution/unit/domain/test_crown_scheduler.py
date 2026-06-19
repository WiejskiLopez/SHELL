"""Tests for InMemoryCrownScheduler."""

from __future__ import annotations

from shell.domain.execution.ports.crown_scheduler import SubGraphChildStatus
from shell.domain.execution.value_objects.ids import GraphExecutionId
from shell.infrastructure.execution.orchestration.in_memory_crown_scheduler import (
    InMemoryCrownScheduler,
)


class TestInMemoryCrownScheduler:
    async def test_register_child(self) -> None:
        scheduler = InMemoryCrownScheduler()
        parent_id = GraphExecutionId("parent-1")
        child_id = GraphExecutionId("child-1")

        await scheduler.register_child(parent_id, child_id)

        children = await scheduler.get_children(parent_id)
        assert len(children) == 1
        assert children[0].child_graph_execution_id == child_id
        assert children[0].status == "pending"

    async def test_mark_waiting(self) -> None:
        scheduler = InMemoryCrownScheduler()
        graph_id = GraphExecutionId("graph-1")

        await scheduler.mark_waiting(graph_id)

        assert graph_id.value in scheduler._waiting

    async def test_on_child_completed(self) -> None:
        scheduler = InMemoryCrownScheduler()
        parent_id = GraphExecutionId("parent-1")
        child_id = GraphExecutionId("child-1")
        await scheduler.register_child(parent_id, child_id)

        result = {"output": "done"}
        children = await scheduler.on_child_completed(child_id, result)

        assert len(children) == 1
        assert children[0].status == "completed"
        assert children[0].result == result

    async def test_on_child_failed(self) -> None:
        scheduler = InMemoryCrownScheduler()
        parent_id = GraphExecutionId("parent-1")
        child_id = GraphExecutionId("child-1")
        await scheduler.register_child(parent_id, child_id)

        children = await scheduler.on_child_failed(child_id, "error occurred")

        assert len(children) == 1
        assert children[0].status == "failed"

    async def test_has_all_children_completed_no_children(self) -> None:
        scheduler = InMemoryCrownScheduler()
        parent_id = GraphExecutionId("parent-1")

        result = await scheduler.has_all_children_completed(parent_id)
        assert result is True

    async def test_has_all_children_completed_pending(self) -> None:
        scheduler = InMemoryCrownScheduler()
        parent_id = GraphExecutionId("parent-1")
        child_id = GraphExecutionId("child-1")
        await scheduler.register_child(parent_id, child_id)

        result = await scheduler.has_all_children_completed(parent_id)
        assert result is False

    async def test_has_all_children_completed_all_done(self) -> None:
        scheduler = InMemoryCrownScheduler()
        parent_id = GraphExecutionId("parent-1")
        child1 = GraphExecutionId("child-1")
        child2 = GraphExecutionId("child-2")
        await scheduler.register_child(parent_id, child1)
        await scheduler.register_child(parent_id, child2)

        await scheduler.on_child_completed(child1)
        await scheduler.on_child_completed(child2)

        result = await scheduler.has_all_children_completed(parent_id)
        assert result is True

    async def test_get_pending_children(self) -> None:
        scheduler = InMemoryCrownScheduler()
        parent_id = GraphExecutionId("parent-1")
        child1 = GraphExecutionId("child-1")
        child2 = GraphExecutionId("child-2")
        await scheduler.register_child(parent_id, child1)
        await scheduler.register_child(parent_id, child2)

        await scheduler.on_child_completed(child1)

        pending = await scheduler.get_pending_children(parent_id)
        assert len(pending) == 1
        assert pending[0] == child2
