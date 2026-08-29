"""Kontrakt repozytorium node_execution — spójna semantyka get_next_pending między adapterami.

Adapter SQL i adapter in-memory muszą zwracać ten sam najbliższy węzeł PENDING
(deterministycznie wg kolejności węzła) dla danego graph_execution_id.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import String

from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.execution_service.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_order import (
    NodeOrder,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_type import (
    NodeType,
)
from shell.execution_service.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.execution_service.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.models.node_execution import (
    NodeExecutionModel,
)
from shell.execution_service.infrastructure.execution.node_link_execution.persistence.sql.models.node_link_execution import (
    NodeLinkExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.execution_service.infrastructure.execution.node_link_execution.persistence.memory.in_memory_node_link_execution_repository import (
        InMemoryNodeLinkExecutionRepository,
    )

_GRAPH = GraphExecutionId("graph-contract")
_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _node_db_row(node_id: str, order: int) -> NodeExecutionModel:

    return NodeExecutionModel(
        id=node_id,
        position=order,
        node_type="test",
        created_at=_NOW,
        status="PENDING",
    )


def _link_db_row(node_id: str) -> NodeLinkExecutionModel:
    return NodeLinkExecutionModel(
        id=f"link-{node_id}",
        graph_execution_id=_GRAPH.value,
        node_execution_id=node_id,
    )


def _node_entity(node_id: str, order: int) -> NodeExecution:
    return NodeExecution.new(
        id=NodeExecutionId(node_id),
        order=NodeOrder(order),
        node_type=NodeType("test"),
        now=CreatedAt.from_datetime(_NOW),
    )


def _memory_link(node_id: str) -> NodeLinkExecution:
    return NodeLinkExecution.create(
        id_=NodeLinkExecutionId(f"link-{node_id}"),
        graph_execution_id=_GRAPH,
        node_execution_id=NodeExecutionId(node_id),
        now=CreatedAt.from_datetime(_NOW),
    )


async def _clean_sql(session_factory: async_sessionmaker) -> None:
    from sqlalchemy import delete

    async with session_factory() as session:
        await session.execute(
            delete(NodeLinkExecutionModel).where(
                NodeLinkExecutionModel.graph_execution_id == _GRAPH.value
            )
        )
        await session.execute(
            delete(NodeExecutionModel).where(NodeExecutionModel.node_type == "test")
        )
        await session.commit()


class TestMemoryGetNextPending:
    async def test_returns_lowest_order_pending(self) -> None:
        from shell.execution_service.infrastructure.execution.node_execution.persistence.memory.in_memory_node_execution_repository import (
            InMemoryNodeExecutionRepository,
        )
        from shell.execution_service.infrastructure.execution.node_link_execution.persistence.memory.in_memory_node_link_execution_repository import (
            InMemoryNodeLinkExecutionRepository,
        )

        node_repo = InMemoryNodeExecutionRepository()
        link_repo: InMemoryNodeLinkExecutionRepository = InMemoryNodeLinkExecutionRepository()
        node_repo.set_link_repository(link_repo)
        for node_id, order in (("n3", 3), ("n1", 1), ("n2", 2)):
            await node_repo.save(_node_entity(node_id, order))
            await link_repo.save(_memory_link(node_id))

        result = await node_repo.get_next_pending(_GRAPH)
        assert result is not None
        assert result.id.value == "n1"

    async def test_skips_running_node(self) -> None:
        from shell.execution_service.infrastructure.execution.node_execution.persistence.memory.in_memory_node_execution_repository import (
            InMemoryNodeExecutionRepository,
        )
        from shell.execution_service.infrastructure.execution.node_link_execution.persistence.memory.in_memory_node_link_execution_repository import (
            InMemoryNodeLinkExecutionRepository,
        )

        node_repo = InMemoryNodeExecutionRepository()
        link_repo: InMemoryNodeLinkExecutionRepository = InMemoryNodeLinkExecutionRepository()
        node_repo.set_link_repository(link_repo)
        n1 = _node_entity("n1", 1)
        n1.start()
        await node_repo.save(n1)
        await link_repo.save(_memory_link("n1"))
        await node_repo.save(_node_entity("n2", 2))
        await link_repo.save(_memory_link("n2"))

        result = await node_repo.get_next_pending(_GRAPH)
        assert result is not None
        assert result.id.value == "n2"

    async def test_returns_none_when_no_pending(self) -> None:
        from shell.execution_service.infrastructure.execution.node_execution.persistence.memory.in_memory_node_execution_repository import (
            InMemoryNodeExecutionRepository,
        )
        from shell.execution_service.infrastructure.execution.node_link_execution.persistence.memory.in_memory_node_link_execution_repository import (
            InMemoryNodeLinkExecutionRepository,
        )

        node_repo = InMemoryNodeExecutionRepository()
        link_repo: InMemoryNodeLinkExecutionRepository = InMemoryNodeLinkExecutionRepository()
        node_repo.set_link_repository(link_repo)
        n1 = _node_entity("n1", 1)
        n1.start()
        await node_repo.save(n1)
        await link_repo.save(_memory_link("n1"))

        assert await node_repo.get_next_pending(_GRAPH) is None


class TestSqlGetNextPending:
    async def test_returns_lowest_order_pending(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.repositories.sql_node_execution_repository import (
            SqlNodeExecutionRepository,
        )

        await _clean_sql(session_factory)
        async with session_factory() as session:
            session.add(_node_db_row("n3", 3))
            session.add(_link_db_row("n3"))
            session.add(_node_db_row("n1", 1))
            session.add(_link_db_row("n1"))
            session.add(_node_db_row("n2", 2))
            session.add(_link_db_row("n2"))
            await session.commit()

        async with session_factory() as session:
            repo = SqlNodeExecutionRepository(session)
            result = await repo.get_next_pending(_GRAPH)
        assert result is not None
        assert result.id.value == "n1"

    async def test_filters_status_and_orders(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.repositories.sql_node_execution_repository import (
            SqlNodeExecutionRepository,
        )

        await _clean_sql(session_factory)
        async with session_factory() as session:
            running = _node_db_row("n1", 1)
            running.status = "RUNNING"
            session.add(running)
            session.add(_link_db_row("n1"))
            session.add(_node_db_row("n2", 2))
            session.add(_link_db_row("n2"))
            await session.commit()

        async with session_factory() as session:
            repo = SqlNodeExecutionRepository(session)
            result = await repo.get_next_pending(_GRAPH)
        assert result is not None
        assert result.id.value == "n2"

    async def test_returns_none_when_no_pending(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.repositories.sql_node_execution_repository import (
            SqlNodeExecutionRepository,
        )

        await _clean_sql(session_factory)
        async with session_factory() as session:
            running = _node_db_row("n1", 1)
            running.status = "COMPLETED"
            session.add(running)
            session.add(_link_db_row("n1"))
            await session.commit()

        async with session_factory() as session:
            repo = SqlNodeExecutionRepository(session)
            result = await repo.get_next_pending(_GRAPH)
        assert result is None

    async def test_save_get_by_id_round_trip_preserves_state(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        """HIGH-04/MEDIUM-01: entity -> model -> DB -> model -> entity zachowuje stan."""
        from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.repositories.sql_node_execution_repository import (
            SqlNodeExecutionRepository,
        )

        await _clean_sql(session_factory)
        node = _node_entity("roundtrip-1", 4)
        node.start()

        async with session_factory() as session:
            repo = SqlNodeExecutionRepository(session)
            await repo.save(node)
            await session.commit()

        async with session_factory() as session:
            repo = SqlNodeExecutionRepository(session)
            restored = await repo.get_by_id(NodeExecutionId("roundtrip-1"))
            assert restored is not None

        assert restored.id.value == node.id.value
        assert restored.order.value == node.order.value
        assert restored.node_type.value == node.node_type.value
        assert restored.status is node.status

    async def test_model_entity_round_trip_matches_sql_column(self) -> None:
        """HIGH-04: migracja i ORM ds. status zgodne — kolumna status 50 znaków."""
        from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.models.node_execution import (
            NodeExecutionModel,
        )
        from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.repositories.sql_node_execution_repository import (
            _node_execution_entity_to_model,
        )

        node = _node_entity("col-1", 1)
        model = _node_execution_entity_to_model(node)

        assert isinstance(NodeExecutionModel.__table__.c.status.type, String)
        assert NodeExecutionModel.__table__.c.status.type.length == 50
        assert model.status == node.status.value
