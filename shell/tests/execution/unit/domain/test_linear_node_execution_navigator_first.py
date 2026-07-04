from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.domain.execution.services.node_execution_navigator import (
    LinearNodeExecutionNavigator,
)
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    NodeExecutionId,
    TaskExecutionId,
)
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_node_link_execution_repository import (
    InMemoryNodeLinkExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_node_transition_execution_repository import (
    InMemoryNodeTransitionExecutionRepository,
)


class TestLinearNodeExecutionNavigatorFirst:
    async def test_first_returns_lowest_position(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            NodeExecution(
                id=NodeExecutionId("b"),
                position=NodeOrder(1),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            NodeExecution(
                id=NodeExecutionId("a"),
                position=NodeOrder(0),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            NodeExecution(
                id=NodeExecutionId("c"),
                position=NodeOrder(2),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
        ]
        node_repo = InMemoryNodeExecutionRepository()
        link_repo = InMemoryNodeLinkExecutionRepository()
        node_repo.set_link_repo(link_repo)
        for n in nodes:
            await node_repo.save(n)
            await link_repo.save(
                NodeLinkExecution(
                    id=NodeLinkExecutionId.generate(),
                    graph_execution_id=ge.id,
                    node_execution_id=n.id,
                )
            )
        transition_repo = InMemoryNodeTransitionExecutionRepository()

        nav = LinearNodeExecutionNavigator()
        result = await nav.first_async(ge, node_repo, transition_repo)
        assert result is not None
        assert result.id == NodeExecutionId("a")

    async def test_first_on_empty_graph_returns_none(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        node_repo = InMemoryNodeExecutionRepository()
        transition_repo = InMemoryNodeTransitionExecutionRepository()

        nav = LinearNodeExecutionNavigator()
        assert await nav.first_async(ge, node_repo, transition_repo) is None

    async def test_first_handles_unsorted_input(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            NodeExecution(
                id=NodeExecutionId("z"),
                position=NodeOrder(5),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            NodeExecution(
                id=NodeExecutionId("y"),
                position=NodeOrder(3),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            NodeExecution(
                id=NodeExecutionId("x"),
                position=NodeOrder(1),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
        ]
        node_repo = InMemoryNodeExecutionRepository()
        link_repo = InMemoryNodeLinkExecutionRepository()
        node_repo.set_link_repo(link_repo)
        for n in nodes:
            await node_repo.save(n)
            await link_repo.save(
                NodeLinkExecution(
                    id=NodeLinkExecutionId.generate(),
                    graph_execution_id=ge.id,
                    node_execution_id=n.id,
                )
            )
        transition_repo = InMemoryNodeTransitionExecutionRepository()

        nav = LinearNodeExecutionNavigator()
        first = await nav.first_async(ge, node_repo, transition_repo)
        assert first is not None
        assert first.id == NodeExecutionId("x")
