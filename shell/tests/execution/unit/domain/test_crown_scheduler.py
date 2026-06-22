"""Tests for QueryBasedCrownScheduler — stateless, query-based parent-child orchestration."""

from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.task_execution.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
    GraphNodeExecutionDefinition,
)
from shell.infrastructure.execution.orchestration.in_memory_crown_scheduler import (
    QueryBasedCrownScheduler,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.domain.platform.value_objects.mode import Mode


def _make_graph(
    id_: GraphExecutionId,
    task_execution_id: TaskExecutionId,
    parent_id: GraphExecutionId | None = None,
    state_output: dict | None = None,
) -> GraphExecution:
    """Helper: create a minimal GraphExecution for testing."""
    return GraphExecution(
        id=id_,
        task_execution_id=task_execution_id,
        graph_definition_id="test-def",
        parent_graph_execution_id=parent_id,
        state_output=state_output or {},
    )


class TestQueryBasedCrownScheduler:
    async def test_no_parent_returns_none(self) -> None:
        scheduler = QueryBasedCrownScheduler()
        repo = InMemoryGraphExecutionRepository()
        task_id = TaskExecutionId("task-1")
        root = _make_graph(GraphExecutionId("root"), task_id)
        await repo.save(root)

        result = await scheduler.compute_settled_status(
            child_graph_execution_id=GraphExecutionId("root"),
            repo=repo,
        )
        assert result is None

    async def test_child_returns_parent_and_siblings(self) -> None:
        scheduler = QueryBasedCrownScheduler()
        repo = InMemoryGraphExecutionRepository()
        task_id = TaskExecutionId("task-1")
        parent_id = GraphExecutionId("parent")
        child1 = _make_graph(
            GraphExecutionId("child-1"),
            task_id,
            parent_id=parent_id,
            state_output={"out": 1},
        )
        child2 = _make_graph(
            GraphExecutionId("child-2"),
            task_id,
            parent_id=parent_id,
            state_output={"out": 2},
        )

        await repo.save(child1)
        await repo.save(child2)

        result = await scheduler.compute_settled_status(
            child_graph_execution_id=GraphExecutionId("child-1"),
            repo=repo,
        )
        assert result is not None
        assert result.parent_graph_execution_id == parent_id
        assert len(result.children_statuses) == 2
        ids = {s.child_graph_execution_id for s in result.children_statuses}
        assert ids == {GraphExecutionId("child-1"), GraphExecutionId("child-2")}

    async def test_unknown_graph_returns_none(self) -> None:
        scheduler = QueryBasedCrownScheduler()
        repo = InMemoryGraphExecutionRepository()

        result = await scheduler.compute_settled_status(
            child_graph_execution_id=GraphExecutionId("nonexistent"),
            repo=repo,
        )
        assert result is None
