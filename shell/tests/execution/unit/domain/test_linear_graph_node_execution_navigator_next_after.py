from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.services.graph_node_execution_navigator import (
    LinearGraphNodeExecutionNavigator,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
)
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


class TestLinearGraphNodeExecutionNavigatorNextAfter:
    async def test_next_after_returns_following_node(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
        )
        nodes = [
            GraphNodeExecution(
                id=GraphNodeExecutionId("a"), position=NodeOrder(0), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("a"), position=NodeOrder(0), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("b"), position=NodeOrder(1), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
        ]
        for n in nodes:
            n._graph_execution_id = ge.id
        node_repo = InMemoryGraphNodeExecutionRepository()  # type: ignore[abstract]
        for n in nodes:
            await node_repo.save(n)
        transition_repo = InMemoryGraphNodeTransitionExecutionRepository()

        nav = LinearGraphNodeExecutionNavigator()
        nxt = list(await nav.next_after_async(ge, GraphNodeExecutionId("a"), node_repo, transition_repo))
        assert len(nxt) == 1
        assert nxt[0].id == GraphNodeExecutionId("b")

    async def test_next_after_last_node_returns_empty(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
        )
        nodes = [
            GraphNodeExecution(
                id=GraphNodeExecutionId("a"), position=NodeOrder(0), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("b"), position=NodeOrder(1), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
        ]
        for n in nodes:
            n._graph_execution_id = ge.id
        node_repo = InMemoryGraphNodeExecutionRepository()  # type: ignore[abstract]
        for n in nodes:
            await node_repo.save(n)
        transition_repo = InMemoryGraphNodeTransitionExecutionRepository()

        nav = LinearGraphNodeExecutionNavigator()
        assert list(await nav.next_after_async(ge, GraphNodeExecutionId("b"), node_repo, transition_repo)) == []

    async def test_next_after_unknown_node_returns_empty(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
        )
        nodes = [
            GraphNodeExecution(
                id=GraphNodeExecutionId("a"), position=NodeOrder(0), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
        ]
        for n in nodes:
            n._graph_execution_id = ge.id
        node_repo = InMemoryGraphNodeExecutionRepository()  # type: ignore[abstract]
        for n in nodes:
            await node_repo.save(n)
        transition_repo = InMemoryGraphNodeTransitionExecutionRepository()

        nav = LinearGraphNodeExecutionNavigator()
        assert list(await nav.next_after_async(ge, GraphNodeExecutionId("ghost"), node_repo, transition_repo)) == []

    async def test_next_after_respects_position_ordering(self) -> None:
        ge = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=TaskExecutionId.generate(),
        )
        nodes = [
            GraphNodeExecution(
                id=GraphNodeExecutionId("c"), position=NodeOrder(2), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("a"), position=NodeOrder(0), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
            GraphNodeExecution(
                id=GraphNodeExecutionId("b"), position=NodeOrder(1), mode=Mode("agent"), role=NodeRole.AGENT, node_type=NodeType("agent"),
            ),
        ]
        for n in nodes:
            n._graph_execution_id = ge.id
        node_repo = InMemoryGraphNodeExecutionRepository()  # type: ignore[abstract]
        for n in nodes:
            await node_repo.save(n)
        transition_repo = InMemoryGraphNodeTransitionExecutionRepository()

        nav = LinearGraphNodeExecutionNavigator()
        nxt = list(await nav.next_after_async(ge, GraphNodeExecutionId("a"), node_repo, transition_repo))
        assert nxt and nxt[0].id == GraphNodeExecutionId("b")
        nxt2 = list(await nav.next_after_async(ge, GraphNodeExecutionId("b"), node_repo, transition_repo))
        assert nxt2 and nxt2[0].id == GraphNodeExecutionId("c")
