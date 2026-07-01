from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.services.graph_node_execution_navigator import (
    LinearGraphNodeExecutionNavigator,
)
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
)
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_repository import (
    InMemoryGraphNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_transition_execution_repository import (
    InMemoryGraphNodeTransitionExecutionRepository,
)


class TestLinearGraphNodeExecutionNavigatorFirst:
    async def test_first_returns_lowest_position(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            GraphNodeExecution(
                id=GraphNodeExecutionId("b"),
                position=NodeOrder(1),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("a"),
                position=NodeOrder(0),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("c"),
                position=NodeOrder(2),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
        ]
        for n in nodes:
            n._graph_execution_id = ge.id
        node_repo = InMemoryGraphNodeExecutionRepository()
        for n in nodes:
            await node_repo.save(n)
        transition_repo = InMemoryGraphNodeTransitionExecutionRepository()

        nav = LinearGraphNodeExecutionNavigator()
        result = await nav.first_async(ge, node_repo, transition_repo)
        assert result is not None
        assert result.id == GraphNodeExecutionId("a")

    async def test_first_on_empty_graph_returns_none(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        node_repo = InMemoryGraphNodeExecutionRepository()
        transition_repo = InMemoryGraphNodeTransitionExecutionRepository()

        nav = LinearGraphNodeExecutionNavigator()
        assert await nav.first_async(ge, node_repo, transition_repo) is None

    async def test_first_handles_unsorted_input(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            GraphNodeExecution(
                id=GraphNodeExecutionId("z"),
                position=NodeOrder(5),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("y"),
                position=NodeOrder(3),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("x"),
                position=NodeOrder(1),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
        ]
        for n in nodes:
            n._graph_execution_id = ge.id
        node_repo = InMemoryGraphNodeExecutionRepository()
        for n in nodes:
            await node_repo.save(n)
        transition_repo = InMemoryGraphNodeTransitionExecutionRepository()

        nav = LinearGraphNodeExecutionNavigator()
        first = await nav.first_async(ge, node_repo, transition_repo)
        assert first is not None
        assert first.id == GraphNodeExecutionId("x")
