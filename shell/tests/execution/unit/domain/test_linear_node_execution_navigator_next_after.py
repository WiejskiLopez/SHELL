from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.domain.execution.services.node_execution_navigator import (
    LinearNodeExecutionNavigator,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    NodeExecutionId,
    TaskExecutionId,
)
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_node_link_execution_repository import (
    InMemoryNodeLinkExecutionRepository,
)


class TestLinearNodeExecutionNavigatorNextAfter:
    async def test_next_after_returns_following_node(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            NodeExecution(
                id=NodeExecutionId("a"),
                position=NodeOrder(0),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            NodeExecution(
                id=NodeExecutionId("b"),
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
        nav = LinearNodeExecutionNavigator()
        nxt = list(
            await nav.next_after_async(ge, NodeExecutionId("a"), node_repo)
        )
        assert len(nxt) == 1
        assert nxt[0].id == NodeExecutionId("b")

    async def test_next_after_last_node_returns_empty(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            NodeExecution(
                id=NodeExecutionId("a"),
                position=NodeOrder(0),
                mode=Mode("agent"),
                role=NodeRole.AGENT,
                node_type=NodeType("agent"),

            ),
            NodeExecution(
                id=NodeExecutionId("b"),
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
        nav = LinearNodeExecutionNavigator()
        assert (
            list(
                await nav.next_after_async(
                    ge, NodeExecutionId("b"), node_repo
                )
            )
            == []
        )

    async def test_next_after_unknown_node_returns_empty(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            NodeExecution(
                id=NodeExecutionId("a"),
                position=NodeOrder(0),
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
        nav = LinearNodeExecutionNavigator()
        assert (
            list(
                await nav.next_after_async(
                    ge, NodeExecutionId("ghost"), node_repo
                )
            )
            == []
        )

    async def test_next_after_respects_position_ordering(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        nodes = [
            NodeExecution(
                id=NodeExecutionId("c"),
                position=NodeOrder(2),
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
                id=NodeExecutionId("b"),
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
        nav = LinearNodeExecutionNavigator()
        nxt = list(
            await nav.next_after_async(ge, NodeExecutionId("a"), node_repo)
        )
        assert nxt and nxt[0].id == NodeExecutionId("b")
        nxt2 = list(
            await nav.next_after_async(ge, NodeExecutionId("b"), node_repo)
        )
        assert nxt2 and nxt2[0].id == NodeExecutionId("c")
